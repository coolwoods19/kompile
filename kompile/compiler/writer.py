"""Write TieredWiki to local markdown files.

Directory structure:
  wiki/
  ├── index.md              # Master lightweight index across all tiers
  ├── profile.md            # Knowledge shape overview with depth bars
  ├── deep/
  │   └── {domain_slug}/
  │       └── {article_id}.md
  ├── active/
  │   └── {topic_slug}.md
  ├── surface/
  │   └── {source_id}.md
  ├── concepts.md
  ├── insights.md
  └── gaps.md
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

from kompile.models import TieredWiki, WikiCompilation, ActiveNote, SurfaceNote
from kompile.utils import slugify

# Tier emoji labels
TIER_ICONS = {"deep": "⚡", "active": "🎯", "surface": "✈️"}
MAX_BAR_LEN = 12


def write_wiki(wiki: TieredWiki, wiki_dir: Path) -> None:
    wiki_dir.mkdir(parents=True, exist_ok=True)
    (wiki_dir / "deep").mkdir(exist_ok=True)
    (wiki_dir / "active").mkdir(exist_ok=True)
    (wiki_dir / "surface").mkdir(exist_ok=True)

    _write_deep_domains(wiki, wiki_dir)
    _write_active_notes(wiki, wiki_dir)
    _write_surface_notes(wiki, wiki_dir)
    _write_index(wiki, wiki_dir)
    _write_profile(wiki, wiki_dir)
    _write_concepts(wiki, wiki_dir)
    _write_insights(wiki, wiki_dir)
    _write_gaps(wiki, wiki_dir)


# ---------------------------------------------------------------------------
# Deep domains
# ---------------------------------------------------------------------------

def _write_deep_domains(wiki: TieredWiki, wiki_dir: Path) -> None:
    for domain_wiki in wiki.deep_domains:
        domain_slug = slugify(domain_wiki.domain_name or domain_wiki.title)
        domain_dir = wiki_dir / "deep" / domain_slug
        domain_dir.mkdir(parents=True, exist_ok=True)
        for article in domain_wiki.articles:
            _write_deep_article(article, domain_wiki.domain_name or domain_wiki.title, domain_dir)


def _write_deep_article(article, domain_name: str, domain_dir: Path) -> None:
    fm_sources = [dataclasses.asdict(s) for s in article.sources]
    frontmatter = (
        "---\n"
        f'title: "{_escape_yaml(article.title)}"\n'
        f"tier: deep\n"
        f'domain: "{_escape_yaml(domain_name)}"\n'
        "sources:\n"
    )
    for s in fm_sources:
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
            f"[{bl}](../../{bl}.md)" for bl in article.backlinks
        ) + "\n"

    (domain_dir / f"{article.id}.md").write_text(frontmatter + body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Active notes
# ---------------------------------------------------------------------------

def _write_active_notes(wiki: TieredWiki, wiki_dir: Path) -> None:
    for note in wiki.active_notes:
        _write_active_note(note, wiki_dir / "active")


def _write_active_note(note: ActiveNote, active_dir: Path) -> None:
    topic_slug = slugify(note.topic)
    fm_sources = [dataclasses.asdict(s) for s in note.sources]
    frontmatter = (
        "---\n"
        f'title: "{_escape_yaml(note.topic)}"\n'
        "tier: active\n"
        "sources:\n"
    )
    for s in fm_sources:
        frontmatter += (
            f"  - platform: {s['platform']}\n"
            f"    title: \"{_escape_yaml(s['title'])}\"\n"
            f"    date: {s['date']}\n"
        )
    if note.concepts:
        frontmatter += f"concepts: [{', '.join(note.concepts)}]\n"
    if note.related_domains:
        frontmatter += f"related_domains: [{', '.join(note.related_domains)}]\n"
    frontmatter += "---\n\n"

    body = f"# {note.topic}\n\n{note.note}\n"
    (active_dir / f"{topic_slug}.md").write_text(frontmatter + body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Surface notes
# ---------------------------------------------------------------------------

def _write_surface_notes(wiki: TieredWiki, wiki_dir: Path) -> None:
    for note in wiki.surface_notes:
        _write_surface_note(note, wiki_dir / "surface")


def _write_surface_note(note: SurfaceNote, surface_dir: Path) -> None:
    frontmatter = (
        "---\n"
        f'title: "{_escape_yaml(note.title)}"\n'
        f"tier: surface\n"
        f"platform: {note.platform}\n"
        f"date: {note.date}\n"
        f"topics: [{', '.join(note.topics)}]\n"
        "---\n\n"
    )
    body = f"# {note.title}\n\n**Summary:** {note.summary}\n\n"
    body += f"_Archived from {note.platform} on {note.date}. Single source — not compiled._\n"
    (surface_dir / f"{note.source_id}.md").write_text(frontmatter + body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Master index (lightweight, for MCP)
# ---------------------------------------------------------------------------

def _write_index(wiki: TieredWiki, wiki_dir: Path) -> None:
    lines = ["# Knowledge Profile — Index\n\n"]
    lines.append(
        "_Lightweight index optimised for AI context loading. "
        "Tier indicators: ⚡ Deep Domain | 🎯 Active Topic | ▪ Surface Note._\n"
    )

    # Deep domains
    if wiki.deep_domains:
        lines.append("\n## Deep Domains\n")
    for domain_wiki in wiki.deep_domains:
        domain_slug = slugify(domain_wiki.domain_name or domain_wiki.title)
        domain_name = domain_wiki.domain_name or domain_wiki.title
        lines.append(f"\n### ⚡ {domain_name}\n\n")
        for article in domain_wiki.articles:
            concepts_str = ", ".join(article.concepts[:4]) if article.concepts else ""
            concepts_part = f" | {concepts_str}" if concepts_str else ""
            source_titles = ", ".join(f'"{s.title}"' for s in article.sources[:3])
            sources_part = f" | sources: {source_titles}" if source_titles else ""
            first_line = article.content.split("\n")[0][:100].strip()
            lines.append(
                f"- **[{article.title}](deep/{domain_slug}/{article.id}.md)**"
                f"{concepts_part}{sources_part} — {first_line}\n"
            )

    # Active topics
    if wiki.active_notes:
        lines.append("\n## Active Topics\n")
    for note in wiki.active_notes:
        topic_slug = slugify(note.topic)
        concepts_str = ", ".join(note.concepts[:4]) if note.concepts else ""
        concepts_part = f" | {concepts_str}" if concepts_str else ""
        source_titles = ", ".join(f'"{s.title}"' for s in note.sources[:3])
        sources_part = f" | sources: {source_titles}" if source_titles else ""
        first_line = note.note.split("\n")[0][:100].strip()
        related = f" | related: {', '.join(note.related_domains)}" if note.related_domains else ""
        lines.append(
            f"- **🎯 [{note.topic}](active/{topic_slug}.md)**"
            f"{concepts_part}{sources_part}{related} — {first_line}\n"
        )

    # Surface notes
    if wiki.surface_notes:
        lines.append("\n## Surface Notes\n\n")
        surface_entries = [f"▪ {n.title} ({n.platform}, {n.date})" for n in wiki.surface_notes]
        lines.append(" | ".join(surface_entries) + "\n")

    (wiki_dir / "index.md").write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Profile.md — knowledge shape overview
# ---------------------------------------------------------------------------

def _write_profile(wiki: TieredWiki, wiki_dir: Path) -> None:
    lines = ["# Knowledge Profile\n\n"]

    if wiki.deep_domains:
        lines.append("## Deep Domains\n\n")
        for domain_wiki in wiki.deep_domains:
            name = domain_wiki.domain_name or domain_wiki.title
            # Count unique sources across all articles
            source_titles = set()
            for art in domain_wiki.articles:
                for s in art.sources:
                    source_titles.add(s.title)
            src_count = len(source_titles)
            art_count = len(domain_wiki.articles)
            bar = "█" * min(src_count, MAX_BAR_LEN)
            lines.append(f"- ⚡ {name:<30} {bar:<12} {src_count} source{'s' if src_count != 1 else ''}, {art_count} article{'s' if art_count != 1 else ''}\n")
        lines.append("\n")

    if wiki.active_notes:
        lines.append("## Active Topics\n\n")
        for note in wiki.active_notes:
            src_count = len(note.sources)
            bar = "█" * min(src_count, MAX_BAR_LEN)
            lines.append(f"- 🎯 {note.topic:<30} {bar:<12} {src_count} source{'s' if src_count != 1 else ''}, 1 note\n")
        lines.append("\n")

    if wiki.surface_notes:
        lines.append("## Surface Notes\n\n")
        surface_parts = [f"▪ {n.title} (1 source)" for n in wiki.surface_notes]
        lines.append(" | ".join(surface_parts) + "\n\n")

    if wiki.cross_topic_concepts:
        lines.append("## Cross-Domain Concepts\n\n")
        for c in wiki.cross_topic_concepts:
            lines.append(f"- **{c.name}** — appears in: {', '.join(c.appears_in)}\n")
        lines.append("\n")

    (wiki_dir / "profile.md").write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Concepts, insights, gaps
# ---------------------------------------------------------------------------

def _write_concepts(wiki: TieredWiki, wiki_dir: Path) -> None:
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


def _write_insights(wiki: TieredWiki, wiki_dir: Path) -> None:
    lines = ["# Cross-Domain Insights\n\n"]

    # Per-domain insights
    for domain_wiki in wiki.deep_domains:
        for ins in domain_wiki.insights:
            lines.append(f"- {ins.text}\n")
            if ins.sources:
                lines.append(f"  _Sources: {', '.join(ins.sources)}_\n")
            lines.append("\n")

    # Global cross-domain insights
    for ins in wiki.insights:
        lines.append(f"- {ins.text}\n")
        if ins.sources:
            lines.append(f"  _Sources: {', '.join(ins.sources)}_\n")
        lines.append("\n")

    if not wiki.deep_domains and not wiki.insights:
        lines.append("_No cross-domain insights identified yet._\n")
    (wiki_dir / "insights.md").write_text("".join(lines), encoding="utf-8")


def _write_gaps(wiki: TieredWiki, wiki_dir: Path) -> None:
    lines = ["# Suggested Gaps\n\n"]
    all_gaps = list(wiki.suggested_gaps)
    for domain_wiki in wiki.deep_domains:
        all_gaps.extend(domain_wiki.suggested_gaps)
    for gap in all_gaps:
        lines.append(f"## {gap.gap}\n\n{gap.detail}\n\n")
    if not all_gaps:
        lines.append("_No gaps identified yet._\n")
    (wiki_dir / "gaps.md").write_text("".join(lines), encoding="utf-8")


def _escape_yaml(s: str) -> str:
    return s.replace('"', '\\"')


# ---------------------------------------------------------------------------
# Helpers for incremental path (used by cli.py _apply_incremental_patch)
# ---------------------------------------------------------------------------

def _write_articles(wiki: WikiCompilation, articles_dir: Path) -> None:
    """Legacy helper used by the incremental patch path in cli.py."""
    for article in wiki.articles:
        fm_sources = [dataclasses.asdict(s) for s in article.sources]
        frontmatter = (
            "---\n"
            f'title: "{_escape_yaml(article.title)}"\n'
            "sources:\n"
        )
        for s in fm_sources:
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
        (articles_dir / f"{article.id}.md").write_text(frontmatter + body, encoding="utf-8")
