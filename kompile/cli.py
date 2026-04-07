"""KOMPILE CLI — ingest → filter → compile → status."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from kompile.config import load_config
from kompile.state import (
    load_state, save_state,
    state_add_sources, state_add_filter_results, state_add_summaries,
    state_get_summaries, state_unfiltered_source_ids,
    state_add_tier_classifications, state_get_tier_classifications,
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
              type=click.Choice(["claude", "chatgpt", "claude_code", "article", "youtube", "raw", "auto"]),
              default="auto", help="Source type (default: auto-detect)")
@click.pass_context
def ingest(ctx, path, source_type):
    """Parse source files, URLs, or directories and add them to the raw/ staging area."""
    from kompile.ingest import (
        parse_claude_export, parse_chatgpt_export,
        parse_claude_code_directory, parse_raw_file,
        parse_article_url, parse_youtube_url,
    )
    from kompile.ingest.raw import parse_raw_text
    from kompile.ingest.router import route_input

    cfg = ctx.obj["config"]
    root = ctx.obj["root"]
    raw_dir = root / cfg["paths"]["raw"]
    raw_dir.mkdir(exist_ok=True)
    state = load_state(root)

    # Auto-detect type via router
    if source_type == "auto":
        source_type = route_input(path)

    sources = []

    if source_type == "article":
        result = parse_article_url(path)
        if result is None:
            sys.exit(1)
        sources = [result]
        click.echo(f"Fetched article: {result.title}")

    elif source_type == "youtube":
        result = parse_youtube_url(path)
        if result is None:
            sys.exit(1)
        sources = [result]
        click.echo(f"Fetched YouTube transcript: {result.title}")

    else:
        p = Path(path)
        if not p.exists():
            click.echo(f"Error: path does not exist: {path}", err=True)
            sys.exit(1)

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
    """Run Haiku filter on all unfiltered sources, then classify topics into tiers."""
    from kompile.compiler.filter import filter_source
    from kompile.compiler.classify import classify_topics

    cfg = ctx.obj["config"]
    root = ctx.obj["root"]
    raw_dir = root / cfg["paths"]["raw"]
    state = load_state(root)
    client = _get_client(cfg)
    model = cfg["models"]["filter"]

    unfiltered = state_unfiltered_source_ids(state)
    if not unfiltered:
        click.echo("All sources already filtered.")
    else:
        click.echo(f"Filtering {len(unfiltered)} sources with {model}...")

        results = []
        from kompile.models import Source
        for i, sid in enumerate(sorted(unfiltered), 1):
            src_file = raw_dir / f"{sid}.txt"
            if not src_file.exists():
                click.echo(f"  [{i}/{len(unfiltered)}] Skipping {sid} (file not found)")
                continue

            src_data = state["sources"].get(sid, {})
            source = Source(
                id=sid,
                platform=src_data.get("platform", "manual"),
                title=src_data.get("title", sid),
                date=src_data.get("date", ""),
                content=src_file.read_text(encoding="utf-8"),
                url=src_data.get("metadata", {}).get("url"),
                metadata=src_data.get("metadata", {}),
            )

            result = filter_source(source, client, model)
            results.append(result)
            status = "✓ keep" if result.keep else "✗ discard"
            click.echo(f"  [{i}/{len(unfiltered)}] {source.title[:60]} → {status} | {result.summary[:80]}")

        state_add_filter_results(state, results)
        kept = sum(1 for r in results if r.keep)
        click.echo(f"\nFiltered {len(results)} sources: {kept} kept, {len(results)-kept} discarded.")

    # Always re-classify (filter results may have changed)
    click.echo("\nClassifying topics into depth tiers...")
    classifications = classify_topics(state["filter_results"])
    state_add_tier_classifications(state, classifications)
    save_state(root, state)

    deep = sum(1 for v in classifications.values() if v["tier"] == "deep")
    active = sum(1 for v in classifications.values() if v["tier"] == "active")
    surface = sum(1 for v in classifications.values() if v["tier"] == "surface")
    click.echo(f"Topics: {deep} deep domains, {active} active topics, {surface} surface notes")
    click.echo("Run `kompile compile` to generate your knowledge base.")


@cli.command()
@click.option("--incremental", is_flag=True, help="Only process new sources since last compile")
@click.pass_context
def compile(ctx, incremental):
    """Run full tiered compilation pipeline → wiki/ directory."""
    from kompile.models import Source, TieredWiki, SurfaceNote, Concept, Insight, Gap
    from kompile.compiler.filter import filter_source
    from kompile.compiler.classify import classify_topics
    from kompile.compiler.summarize import summarize_source
    from kompile.compiler.compile import (
        compile_wiki_domain, compile_active_topic, compile_cross_domain,
        compile_incremental,
    )
    from kompile.compiler.writer import write_wiki, _write_articles, _write_deep_article
    from kompile.utils import slugify

    cfg = ctx.obj["config"]
    root = ctx.obj["root"]
    raw_dir = root / cfg["paths"]["raw"]
    wiki_dir = root / cfg["paths"]["wiki"]
    state = load_state(root)
    client = _get_client(cfg)

    # ------------------------------------------------------------------ #
    # Step 1: Filter any unfiltered sources
    # ------------------------------------------------------------------ #
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
                content=src_file.read_text(encoding="utf-8"),
                url=src_data.get("metadata", {}).get("url"),
                metadata=src_data.get("metadata", {}),
            )
            result = filter_source(source, client, cfg["models"]["filter"])
            results.append(result)
            status = "✓" if result.keep else "✗"
            click.echo(f"  {status} {source.title[:60]}")
        state_add_filter_results(state, results)
        save_state(root, state)

    # ------------------------------------------------------------------ #
    # Step 2: Classify topics (if not already done or new sources added)
    # ------------------------------------------------------------------ #
    tier_classifications = state_get_tier_classifications(state)
    if not tier_classifications or unfiltered:
        tier_classifications = classify_topics(state["filter_results"])
        state_add_tier_classifications(state, tier_classifications)
        save_state(root, state)

    # ------------------------------------------------------------------ #
    # Step 3: Summarize deep + active sources (skip surface)
    # ------------------------------------------------------------------ #
    # Determine which source IDs need summaries (deep + active tiers only)
    deep_active_sids: set[str] = set()
    for topic, info in tier_classifications.items():
        if info["tier"] in ("deep", "active"):
            deep_active_sids.update(info["sources"])

    unsummarized = {
        sid for sid in deep_active_sids
        if sid in state["filter_results"]
        and state["filter_results"][sid].get("keep")
        and sid not in state["summaries"]
    }

    if unsummarized:
        click.echo(f"\nSummarizing {len(unsummarized)} sources (deep + active only)...")
        new_summaries = []
        for i, sid in enumerate(sorted(unsummarized), 1):
            src_file = raw_dir / f"{sid}.txt"
            if not src_file.exists():
                continue
            src_data = state["sources"].get(sid, {})
            source = Source(
                id=sid, platform=src_data.get("platform", "manual"),
                title=src_data.get("title", sid), date=src_data.get("date", ""),
                content=src_file.read_text(encoding="utf-8"),
                url=src_data.get("metadata", {}).get("url"),
                metadata=src_data.get("metadata", {}),
            )
            click.echo(f"  [{i}/{len(unsummarized)}] Summarizing: {source.title[:60]}...")
            summary = summarize_source(source, client, cfg["models"]["summarize"])
            new_summaries.append(summary)
        state_add_summaries(state, new_summaries)
        save_state(root, state)

    # Build summary lookup
    all_summaries = {s.source_id: s for s in state_get_summaries(state)}

    # ------------------------------------------------------------------ #
    # Incremental path
    # ------------------------------------------------------------------ #
    if incremental and (wiki_dir / "index.md").exists():
        new_sids = unsummarized if 'new_summaries' in dir() else set()
        if not new_sids:
            click.echo("No new sources to incrementally compile.")
            return
        click.echo(f"\nIncrementally compiling {len(new_sids)} new source(s)...")
        for sid in new_sids:
            if sid in all_summaries:
                click.echo(f"  Integrating: {all_summaries[sid].title[:60]}...")
                patch = compile_incremental(all_summaries[sid], wiki_dir, client, cfg["models"]["compile"])
                _apply_incremental_patch(patch, wiki_dir)
        click.echo("Incremental compilation complete.")
        return

    # ------------------------------------------------------------------ #
    # Step 4: Full tiered compilation
    # ------------------------------------------------------------------ #
    known_article_ids: set[str] = set()
    deep_domain_wikis = []
    active_notes = []
    surface_notes = []

    # -- Deep domains --
    deep_topics = {t: info for t, info in tier_classifications.items() if info["tier"] == "deep"}
    if deep_topics:
        click.echo(f"\nCompiling {len(deep_topics)} deep domain(s)...")
    for topic, info in deep_topics.items():
        topic_summaries = [all_summaries[sid] for sid in info["sources"] if sid in all_summaries]
        if not topic_summaries:
            click.echo(f"  Skipping '{topic}' (no summaries available)")
            continue
        click.echo(f"  Compiling deep domain: {topic} ({len(topic_summaries)} summaries)...")
        domain_wiki = compile_wiki_domain(
            topic_summaries, topic, client, cfg["models"]["compile"],
            known_ids=known_article_ids,
            progress_cb=lambda msg: click.echo(f"    {msg}"),
        )
        deep_domain_wikis.append(domain_wiki)

    # -- Active topics --
    active_topics = {t: info for t, info in tier_classifications.items() if info["tier"] == "active"}
    if active_topics:
        click.echo(f"\nCompiling {len(active_topics)} active topic(s)...")
    for topic, info in active_topics.items():
        topic_summaries = [all_summaries[sid] for sid in info["sources"] if sid in all_summaries]
        if not topic_summaries:
            click.echo(f"  Skipping '{topic}' (no summaries available)")
            continue
        click.echo(f"  Compiling active topic: {topic} ({len(topic_summaries)} summaries)...")
        note = compile_active_topic(topic_summaries, topic, client, cfg["models"]["compile"])
        active_notes.append(note)

    # -- Surface notes (no compilation — use Haiku filter summary) --
    surface_topics = {t: info for t, info in tier_classifications.items() if info["tier"] == "surface"}
    for topic, info in surface_topics.items():
        for sid in info["sources"]:
            fr = state["filter_results"].get(sid, {})
            if not fr.get("keep"):
                continue
            src_data = state["sources"].get(sid, {})
            surface_notes.append(SurfaceNote(
                source_id=sid,
                title=src_data.get("title", sid),
                platform=src_data.get("platform", "manual"),
                date=src_data.get("date", ""),
                summary=fr.get("summary", ""),
                topics=fr.get("topics", []),
            ))
    if surface_topics:
        click.echo(f"\n{len(surface_notes)} surface note(s) archived (no compilation needed).")

    if not deep_domain_wikis and not active_notes and not surface_notes:
        click.echo("No kept sources to compile. Import and filter some sources first.")
        return

    # ------------------------------------------------------------------ #
    # Step 5: Cross-domain pass
    # ------------------------------------------------------------------ #
    click.echo("\nRunning cross-domain analysis...")
    lightweight_index = _build_lightweight_index(deep_domain_wikis, active_notes, surface_notes)
    cross_data = compile_cross_domain(lightweight_index, client, cfg["models"]["compile"])

    # Parse cross-domain results
    cross_concepts = [
        Concept(
            name=c.get("concept", c.get("name", "")),
            appears_in=c.get("appears_in", []),
            note=c.get("note", ""),
        )
        for c in cross_data.get("cross_topic_concepts", [])
    ]
    cross_insights = [
        Insight(text=ins["text"], sources=ins.get("sources", []))
        for ins in cross_data.get("insights", [])
    ]
    cross_gaps = [
        Gap(gap=g["gap"], detail=g.get("detail", ""))
        for g in cross_data.get("suggested_gaps", [])
    ]

    # Apply related_domains patches to active notes
    related_map = cross_data.get("active_topic_related_domains", {})
    for note in active_notes:
        topic_slug = slugify(note.topic)
        note.related_domains = related_map.get(topic_slug, related_map.get(note.topic, []))

    # ------------------------------------------------------------------ #
    # Step 6: Write wiki
    # ------------------------------------------------------------------ #
    from kompile.models import TieredWiki
    tiered_wiki = TieredWiki(
        deep_domains=deep_domain_wikis,
        active_notes=active_notes,
        surface_notes=surface_notes,
        cross_topic_concepts=cross_concepts,
        insights=cross_insights,
        suggested_gaps=cross_gaps,
    )

    click.echo(f"\nWriting wiki to {wiki_dir}/...")
    write_wiki(tiered_wiki, wiki_dir)

    # Summary
    total_articles = sum(len(d.articles) for d in deep_domain_wikis)
    click.echo(f"\nDone!")
    click.echo(f"  Deep domains:   {len(deep_domain_wikis)} ({total_articles} articles)")
    click.echo(f"  Active topics:  {len(active_notes)} (1 note each)")
    click.echo(f"  Surface notes:  {len(surface_notes)} (archived)")
    click.echo(f"  Insights:       {len(cross_insights)}")
    click.echo(f"  Suggested gaps: {len(cross_gaps)}")
    click.echo(f"\nTo use with Claude Desktop, start the MCP server:")
    click.echo("  python -m kompile.mcp.server")


def _build_lightweight_index(
    deep_domain_wikis, active_notes, surface_notes
) -> str:
    """Build a lightweight index string (<10K tokens) for the cross-domain pass.

    Contains only titles, one-line summaries, concept tags, and source platforms.
    Does NOT include full article content.
    """
    lines = ["# Knowledge Profile — Lightweight Index\n\n"]

    if deep_domain_wikis:
        lines.append("## Deep Domains\n\n")
    for dw in deep_domain_wikis:
        lines.append(f"### {dw.domain_name}\n\n")
        for art in dw.articles:
            concepts = ", ".join(art.concepts[:5])
            platforms = ", ".join(set(s.platform for s in art.sources))
            first_line = art.content.split("\n")[0][:120].strip()
            lines.append(f"- **{art.title}** | concepts: {concepts} | platforms: {platforms} — {first_line}\n")
        lines.append("\n")

    if active_notes:
        lines.append("## Active Topics\n\n")
    for note in active_notes:
        concepts = ", ".join(note.concepts[:5])
        platforms = ", ".join(set(s.platform for s in note.sources))
        first_line = note.note.split("\n")[0][:120].strip()
        lines.append(f"- **{note.topic}** | concepts: {concepts} | platforms: {platforms} — {first_line}\n")

    if surface_notes:
        lines.append("\n## Surface Notes\n\n")
        for sn in surface_notes:
            lines.append(f"- {sn.title} ({sn.platform}) — {sn.summary}\n")

    return "".join(lines)


def _apply_incremental_patch(patch: dict, wiki_dir: Path) -> None:
    """Apply incremental compilation patch to wiki files (legacy flat structure)."""
    # Try tiered deep/ first, fall back to flat articles/
    deep_dir = wiki_dir / "deep"
    articles_dir = wiki_dir / "articles"

    # Find writable articles directory
    if deep_dir.exists():
        target_dir = deep_dir / "incremental"
        target_dir.mkdir(parents=True, exist_ok=True)
    else:
        target_dir = articles_dir
        target_dir.mkdir(exist_ok=True)

    for art in patch.get("new_articles", []):
        from kompile.models import Article, ArticleSource, WikiCompilation
        from kompile.compiler.writer import _write_articles
        article = Article(
            id=art["id"], title=art["title"],
            sources=[ArticleSource(**s) for s in art.get("sources", [])],
            content=art.get("content", ""), concepts=art.get("concepts", []),
            backlinks=art.get("backlinks", []),
        )
        _write_articles(
            WikiCompilation(title="", articles=[article], domains=[],
                            cross_topic_concepts=[], insights=[], suggested_gaps=[]),
            target_dir,
        )

    for updated in patch.get("updated_articles", []):
        # Search for the article across the wiki
        art_file = None
        for candidate in wiki_dir.glob(f"**/{updated['id']}.md"):
            art_file = candidate
            break
        if art_file and art_file.exists():
            content = art_file.read_text(encoding="utf-8")
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                new_content = parts[0] + "---\n" + parts[1] + "---\n\n" + updated.get("content", "") + "\n"
                art_file.write_text(new_content, encoding="utf-8")

    if patch.get("new_insights"):
        insights_file = wiki_dir / "insights.md"
        existing = insights_file.read_text(encoding="utf-8") if insights_file.exists() else "# Cross-Domain Insights\n\n"
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

    tier_classifications = state_get_tier_classifications(state)
    deep = sum(1 for v in tier_classifications.values() if v["tier"] == "deep")
    active = sum(1 for v in tier_classifications.values() if v["tier"] == "active")
    surface_count = sum(1 for v in tier_classifications.values() if v["tier"] == "surface")

    compiled = (wiki_dir / "index.md").exists()
    deep_articles = list((wiki_dir / "deep").glob("**/*.md")) if (wiki_dir / "deep").exists() else []
    active_notes = list((wiki_dir / "active").glob("*.md")) if (wiki_dir / "active").exists() else []
    surface_notes = list((wiki_dir / "surface").glob("*.md")) if (wiki_dir / "surface").exists() else []

    click.echo("KOMPILE Status")
    click.echo("─" * 40)
    click.echo(f"Sources ingested:    {total_sources}")
    click.echo(f"Sources filtered:    {filtered}/{total_sources}")
    click.echo(f"  → kept:            {kept}")
    click.echo(f"  → discarded:       {filtered - kept}")
    if tier_classifications:
        click.echo(f"Topics classified:   {len(tier_classifications)}")
        click.echo(f"  → deep domains:    {deep}")
        click.echo(f"  → active topics:   {active}")
        click.echo(f"  → surface notes:   {surface_count}")
    click.echo(f"Sources summarized:  {summarized}/{kept}")
    click.echo(f"Wiki compiled:       {'yes' if compiled else 'no'}")
    if compiled:
        click.echo(f"  → deep articles:   {len(deep_articles)}")
        click.echo(f"  → active notes:    {len(active_notes)}")
        click.echo(f"  → surface notes:   {len(surface_notes)}")
    click.echo(f"\nWiki directory:      {wiki_dir}/")


if __name__ == "__main__":
    cli()
