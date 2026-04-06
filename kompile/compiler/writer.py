"""Write WikiCompilation to local markdown files."""
from __future__ import annotations

import dataclasses
from pathlib import Path

from kompile.models import WikiCompilation


def write_wiki(wiki: WikiCompilation, wiki_dir: Path) -> None:
    wiki_dir.mkdir(parents=True, exist_ok=True)
    articles_dir = wiki_dir / "articles"
    articles_dir.mkdir(exist_ok=True)

    _write_articles(wiki, articles_dir)
    _write_index(wiki, wiki_dir)
    _write_concepts(wiki, wiki_dir)
    _write_insights(wiki, wiki_dir)
    _write_gaps(wiki, wiki_dir)
    _write_domains(wiki, wiki_dir)


def _write_articles(wiki: WikiCompilation, articles_dir: Path) -> None:
    for article in wiki.articles:
        frontmatter_sources = [dataclasses.asdict(s) for s in article.sources]
        frontmatter = (
            "---\n"
            f'title: "{_escape_yaml(article.title)}"\n'
            f"sources:\n"
        )
        for s in frontmatter_sources:
            frontmatter += (
                f"  - platform: {s['platform']}\n"
                f"    title: \"{_escape_yaml(s['title'])}\"\n"
                f"    date: {s['date']}\n"
            )
        if article.concepts:
            frontmatter += f"concepts: [{', '.join(article.concepts)}]\n"
        if article.backlinks:
            frontmatter += f"backlinks: [{', '.join(article.backlinks)}]\n"
        frontmatter += "---\n\n"

        body = f"# {article.title}\n\n{article.content}\n"

        if article.backlinks:
            body += "\n---\n\n**Related articles:** " + ", ".join(
                f"[{bl}](../articles/{bl}.md)" for bl in article.backlinks
            ) + "\n"

        (articles_dir / f"{article.id}.md").write_text(
            frontmatter + body, encoding="utf-8"
        )


def _write_index(wiki: WikiCompilation, wiki_dir: Path) -> None:
    lines = [f"# {wiki.title} — Index\n"]
    lines.append(
        "_This index is optimised for AI context loading. "
        "Each entry is one line to keep total size under 1000 tokens._\n"
    )

    for domain in wiki.domains:
        lines.append(f"\n## {domain.name}\n")
        for subtopic in domain.subtopics:
            lines.append(f"\n### {subtopic.name}\n")
            for art_id in subtopic.article_ids:
                art = next((a for a in wiki.articles if a.id == art_id), None)
                if art:
                    concepts_str = ", ".join(art.concepts[:5]) if art.concepts else ""
                    concepts_part = f" | concepts: {concepts_str}" if concepts_str else ""
                    # One-line entry per article
                    first_sentence = art.content.split("\n")[0][:120].strip()
                    lines.append(f"- **[{art.title}](articles/{art_id}.md)**{concepts_part} — {first_sentence}\n")

    # Articles not in any domain
    domain_article_ids = {
        aid
        for d in wiki.domains
        for st in d.subtopics
        for aid in st.article_ids
    }
    orphans = [a for a in wiki.articles if a.id not in domain_article_ids]
    if orphans:
        lines.append("\n## Uncategorised\n")
        for art in orphans:
            lines.append(f"- **[{art.title}](articles/{art.id}.md)**\n")

    (wiki_dir / "index.md").write_text("".join(lines), encoding="utf-8")


def _write_concepts(wiki: WikiCompilation, wiki_dir: Path) -> None:
    lines = ["# Concepts\n\n"]
    for concept in wiki.cross_topic_concepts:
        domains_str = ", ".join(concept.appears_in)
        lines.append(f"## {concept.name}\n\n")
        lines.append(f"**Appears in:** {domains_str}\n\n")
        if concept.note:
            lines.append(f"{concept.note}\n\n")
    if not wiki.cross_topic_concepts:
        lines.append("_No cross-domain concepts identified yet._\n")
    (wiki_dir / "concepts.md").write_text("".join(lines), encoding="utf-8")


def _write_insights(wiki: WikiCompilation, wiki_dir: Path) -> None:
    lines = ["# Cross-Source Insights\n\n"]
    for ins in wiki.insights:
        lines.append(f"- {ins.text}\n")
        if ins.sources:
            lines.append(f"  _Sources: {', '.join(ins.sources)}_\n")
        lines.append("\n")
    if not wiki.insights:
        lines.append("_No cross-source insights identified yet._\n")
    (wiki_dir / "insights.md").write_text("".join(lines), encoding="utf-8")


def _write_gaps(wiki: WikiCompilation, wiki_dir: Path) -> None:
    lines = ["# Suggested Gaps\n\n"]
    for gap in wiki.suggested_gaps:
        lines.append(f"## {gap.gap}\n\n{gap.detail}\n\n")
    if not wiki.suggested_gaps:
        lines.append("_No gaps identified yet._\n")
    (wiki_dir / "gaps.md").write_text("".join(lines), encoding="utf-8")


def _write_domains(wiki: WikiCompilation, wiki_dir: Path) -> None:
    lines = ["# Knowledge Map\n\n"]
    for domain in wiki.domains:
        lines.append(f"## {domain.name}\n\n")
        for subtopic in domain.subtopics:
            lines.append(f"### {subtopic.name}\n\n")
            for art_id in subtopic.article_ids:
                art = next((a for a in wiki.articles if a.id == art_id), None)
                label = art.title if art else art_id
                lines.append(f"- [{label}](articles/{art_id}.md)\n")
            lines.append("\n")
    (wiki_dir / "domains.md").write_text("".join(lines), encoding="utf-8")


def _escape_yaml(s: str) -> str:
    return s.replace('"', '\\"')
