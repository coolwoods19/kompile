"""KOMPILE CLI — ingest → filter → compile → status."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from kompile.config import load_config
from kompile.state import (
    load_state, save_state,
    state_add_sources, state_add_filter_results, state_add_summaries,
    state_get_summaries, state_unfiltered_source_ids, state_unsummarized_kept_ids,
)


def _get_client(cfg: dict):
    import anthropic
    api_key = cfg.get("api_key", "")
    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set. Add it to kompile.yaml or set the env var.", err=True)
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


@click.group()
@click.option("--config", default="kompile.yaml", help="Path to kompile.yaml", show_default=True)
@click.pass_context
def cli(ctx, config):
    """KOMPILE — personal knowledge compiler."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)
    ctx.obj["root"] = Path(".")


@cli.command()
@click.argument("path")
@click.option("--type", "source_type",
              type=click.Choice(["claude", "chatgpt", "claude_code", "raw", "auto"]),
              default="auto", help="Source type (default: auto-detect)")
@click.pass_context
def ingest(ctx, path, source_type):
    """Parse source files and add them to the raw/ staging area."""
    from kompile.ingest import (
        parse_claude_export, parse_chatgpt_export,
        parse_claude_code_directory, parse_raw_file,
    )
    from kompile.ingest.raw import parse_raw_text
    import shutil

    cfg = ctx.obj["config"]
    root = ctx.obj["root"]
    raw_dir = root / cfg["paths"]["raw"]
    raw_dir.mkdir(exist_ok=True)
    state = load_state(root)

    p = Path(path)
    if not p.exists():
        click.echo(f"Error: path does not exist: {path}", err=True)
        sys.exit(1)

    # Auto-detect type
    if source_type == "auto":
        if p.suffix.lower() in (".zip", "") and p.is_file():
            # Heuristic: check filename
            name = p.name.lower()
            if "claude" in name and "code" not in name:
                source_type = "claude"
            elif "chatgpt" in name or "gpt" in name or "openai" in name:
                source_type = "chatgpt"
            else:
                source_type = "claude"  # default
        elif p.is_dir():
            source_type = "claude_code"
        elif p.suffix.lower() in (".md", ".txt"):
            source_type = "raw"
        else:
            source_type = "raw"

    sources = []
    if source_type == "claude":
        sources = parse_claude_export(p)
        click.echo(f"Parsed {len(sources)} Claude conversations.")
    elif source_type == "chatgpt":
        sources = parse_chatgpt_export(p)
        click.echo(f"Parsed {len(sources)} ChatGPT conversations.")
    elif source_type == "claude_code":
        sources = parse_claude_code_directory(p)
        click.echo(f"Parsed {len(sources)} Claude Code files.")
    elif source_type == "raw":
        if p.is_file():
            sources = [parse_raw_file(p)]
            click.echo(f"Parsed raw file: {p.name}")
        else:
            for f in sorted(p.glob("**/*.md")) + sorted(p.glob("**/*.txt")):
                sources.append(parse_raw_file(f))
            click.echo(f"Parsed {len(sources)} raw files.")

    if not sources:
        click.echo("No sources found.")
        return

    # Save content to raw/ directory and register in state
    new_count = 0
    for s in sources:
        dest = raw_dir / f"{s.id}.txt"
        dest.write_text(s.content, encoding="utf-8")
        if s.id not in state["sources"]:
            new_count += 1
    state_add_sources(state, sources)
    save_state(root, state)
    click.echo(f"Added {new_count} new sources ({len(sources) - new_count} already known). Run `kompile filter` next.")


@cli.command("filter")
@click.pass_context
def filter_cmd(ctx):
    """Run Haiku filter on all unfiltered sources."""
    from kompile.ingest.raw import parse_raw_file
    from kompile.compiler.filter import filter_source
    import anthropic

    cfg = ctx.obj["config"]
    root = ctx.obj["root"]
    raw_dir = root / cfg["paths"]["raw"]
    state = load_state(root)
    client = _get_client(cfg)
    model = cfg["models"]["filter"]

    unfiltered = state_unfiltered_source_ids(state)
    if not unfiltered:
        click.echo("All sources already filtered.")
        return

    click.echo(f"Filtering {len(unfiltered)} sources with {model}...")

    results = []
    for i, sid in enumerate(sorted(unfiltered), 1):
        src_file = raw_dir / f"{sid}.txt"
        if not src_file.exists():
            click.echo(f"  [{i}/{len(unfiltered)}] Skipping {sid} (file not found)")
            continue

        src_data = state["sources"].get(sid, {})
        from kompile.models import Source
        source = Source(
            id=sid,
            platform=src_data.get("platform", "manual"),
            title=src_data.get("title", sid),
            date=src_data.get("date", ""),
            content=src_file.read_text(encoding="utf-8"),
            metadata=src_data.get("metadata", {}),
        )

        result = filter_source(source, client, model)
        results.append(result)
        status = "✓ keep" if result.keep else "✗ discard"
        click.echo(f"  [{i}/{len(unfiltered)}] {source.title[:60]} → {status} | {result.summary[:80]}")

    state_add_filter_results(state, results)
    save_state(root, state)
    kept = sum(1 for r in results if r.keep)
    click.echo(f"\nFiltered {len(results)} sources: {kept} kept, {len(results)-kept} discarded.")
    click.echo("Run `kompile compile` to generate your knowledge base.")


@cli.command()
@click.option("--incremental", is_flag=True, help="Only process new sources since last compile")
@click.pass_context
def compile(ctx, incremental):
    """Run full compilation pipeline → wiki/ directory."""
    from kompile.models import Source
    from kompile.compiler.filter import filter_source
    from kompile.compiler.summarize import summarize_source
    from kompile.compiler.compile import compile_wiki, compile_incremental
    from kompile.compiler.writer import write_wiki

    cfg = ctx.obj["config"]
    root = ctx.obj["root"]
    raw_dir = root / cfg["paths"]["raw"]
    wiki_dir = root / cfg["paths"]["wiki"]
    state = load_state(root)
    client = _get_client(cfg)

    # Step 1: Filter any unfiltered sources first
    unfiltered = state_unfiltered_source_ids(state)
    if unfiltered:
        click.echo(f"Filtering {len(unfiltered)} new sources first...")
        results = []
        for sid in sorted(unfiltered):
            src_file = raw_dir / f"{sid}.txt"
            if not src_file.exists():
                continue
            src_data = state["sources"].get(sid, {})
            source = Source(
                id=sid, platform=src_data.get("platform", "manual"),
                title=src_data.get("title", sid), date=src_data.get("date", ""),
                content=src_file.read_text(encoding="utf-8"), metadata=src_data.get("metadata", {}),
            )
            result = filter_source(source, client, cfg["models"]["filter"])
            results.append(result)
            status = "✓" if result.keep else "✗"
            click.echo(f"  {status} {source.title[:60]}")
        state_add_filter_results(state, results)
        save_state(root, state)

    # Step 2: Summarize any unsummarized kept sources
    unsummarized = state_unsummarized_kept_ids(state)
    if unsummarized:
        click.echo(f"\nSummarizing {len(unsummarized)} sources...")
        new_summaries = []
        for i, sid in enumerate(sorted(unsummarized), 1):
            src_file = raw_dir / f"{sid}.txt"
            if not src_file.exists():
                continue
            src_data = state["sources"].get(sid, {})
            source = Source(
                id=sid, platform=src_data.get("platform", "manual"),
                title=src_data.get("title", sid), date=src_data.get("date", ""),
                content=src_file.read_text(encoding="utf-8"), metadata=src_data.get("metadata", {}),
            )
            click.echo(f"  [{i}/{len(unsummarized)}] Summarizing: {source.title[:60]}...")
            summary = summarize_source(source, client, cfg["models"]["summarize"])
            new_summaries.append(summary)
        state_add_summaries(state, new_summaries)
        save_state(root, state)

    summaries = state_get_summaries(state)
    if not summaries:
        click.echo("No kept sources to compile. Import some sources first.")
        return

    # Step 3: Compile
    if incremental and (wiki_dir / "index.md").exists():
        # Only compile the newly summarized sources incrementally
        new_sids = set(s.source_id for s in new_summaries) if unsummarized else set()
        if not new_sids:
            click.echo("No new sources to incrementally compile.")
            return
        click.echo(f"\nIncrementally compiling {len(new_sids)} new source(s)...")
        for summary in [s for s in summaries if s.source_id in new_sids]:
            click.echo(f"  Integrating: {summary.title[:60]}...")
            patch = compile_incremental(summary, wiki_dir, client, cfg["models"]["compile"])
            _apply_incremental_patch(patch, wiki_dir)
        click.echo("Incremental compilation complete.")
    else:
        click.echo(f"\nCompiling {len(summaries)} source summaries into wiki...")
        wiki = compile_wiki(
            summaries, client, cfg["models"]["compile"],
            progress_cb=lambda msg: click.echo(f"  {msg}"),
        )
        write_wiki(wiki, wiki_dir)
        click.echo(f"\nDone! Knowledge base written to {wiki_dir}/")
        click.echo(f"  {len(wiki.articles)} articles")
        click.echo(f"  {len(wiki.insights)} insights")
        click.echo(f"  {len(wiki.suggested_gaps)} suggested gaps")
        click.echo("\nTo use with Claude Desktop, start the MCP server:")
        click.echo("  python -m kompile.mcp.server")


def _apply_incremental_patch(patch: dict, wiki_dir: Path) -> None:
    """Apply incremental compilation patch to wiki files."""
    articles_dir = wiki_dir / "articles"
    articles_dir.mkdir(exist_ok=True)

    for art in patch.get("new_articles", []):
        from kompile.models import Article, ArticleSource
        from kompile.compiler.writer import _write_articles, WikiCompilation, Domain, Concept, Insight, Gap
        article = Article(
            id=art["id"], title=art["title"],
            sources=[ArticleSource(**s) for s in art.get("sources", [])],
            content=art.get("content", ""), concepts=art.get("concepts", []),
            backlinks=art.get("backlinks", []),
        )
        _write_articles(
            WikiCompilation(title="", domains=[], articles=[article],
                            cross_topic_concepts=[], insights=[], suggested_gaps=[]),
            articles_dir,
        )

    for updated in patch.get("updated_articles", []):
        art_file = articles_dir / f"{updated['id']}.md"
        if art_file.exists():
            content = art_file.read_text(encoding="utf-8")
            # Replace content after frontmatter
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                new_content = parts[0] + "---\n" + parts[1] + "---\n\n" + updated.get("content", "") + "\n"
                art_file.write_text(new_content, encoding="utf-8")

    # Append new insights
    if patch.get("new_insights"):
        insights_file = wiki_dir / "insights.md"
        existing = insights_file.read_text(encoding="utf-8") if insights_file.exists() else "# Cross-Source Insights\n\n"
        for ins in patch["new_insights"]:
            existing += f"- {ins}\n\n"
        insights_file.write_text(existing, encoding="utf-8")


@cli.command()
@click.pass_context
def status(ctx):
    """Show pipeline status: sources ingested, filtered, compiled."""
    cfg = ctx.obj["config"]
    root = ctx.obj["root"]
    state = load_state(root)
    wiki_dir = root / cfg["paths"]["wiki"]

    total_sources = len(state["sources"])
    filtered = len(state["filter_results"])
    kept = sum(1 for r in state["filter_results"].values() if r.get("keep"))
    summarized = len(state["summaries"])
    compiled = (wiki_dir / "index.md").exists()

    articles = list((wiki_dir / "articles").glob("*.md")) if compiled else []

    click.echo("KOMPILE Status")
    click.echo("─" * 40)
    click.echo(f"Sources ingested:    {total_sources}")
    click.echo(f"Sources filtered:    {filtered}/{total_sources}")
    click.echo(f"  → kept:            {kept}")
    click.echo(f"  → discarded:       {filtered - kept}")
    click.echo(f"Sources summarized:  {summarized}/{kept}")
    click.echo(f"Wiki compiled:       {'yes' if compiled else 'no'}")
    if compiled:
        click.echo(f"  → articles:        {len(articles)}")
    click.echo(f"\nWiki directory:      {wiki_dir}/")


if __name__ == "__main__":
    cli()
