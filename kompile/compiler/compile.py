"""Core compilation step: cross-source synthesis → wiki articles + knowledge map.

Two-pass strategy (as per product spec Section 4.6):
  Pass 1: per-source summaries (done in summarize.py, ~500 tokens each)
  Pass 2: compile per tier

Tier compilation:
  deep    → compile_wiki_domain(): full articles per domain (one Sonnet call per domain)
  active  → compile_active_topic(): single synthesized note (one Sonnet call per topic)
  surface → no compilation; Haiku summary from filter step is sufficient

Cross-domain pass (after all tiers):
  compile_cross_domain(): one Sonnet call on a lightweight index (<10K tokens)

ARTICLE ID UNIQUENESS GUARANTEE:
  Article IDs must be globally unique across wiki/deep/**/*.md and wiki/active/*.md.
  The MCP get_article tool uses first-match glob — it relies on this invariant.
  compile_wiki_domain() enforces uniqueness by appending -{domain_slug} on collision.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Callable

import anthropic

from kompile.models import (
    ActiveNote, Article, ArticleSource, Concept, Domain,
    Gap, Insight, SourceSummary, Subtopic, WikiCompilation,
)
from kompile.utils import slugify
from .prompts import (
    ACTIVE_COMPILE_SYSTEM, ACTIVE_COMPILE_USER,
    COMPILE_SYSTEM, COMPILE_USER,
    CROSS_DOMAIN_SYSTEM, CROSS_DOMAIN_USER,
    INCREMENTAL_SYSTEM, INCREMENTAL_USER,
)

# At 50% of Sonnet's 200K window; summaries are text, ~4 chars/token
CHUNK_THRESHOLD_CHARS = 320_000  # ~80K tokens input limit for summaries


def _summaries_to_dict(summaries: list[SourceSummary]) -> list[dict]:
    return [dataclasses.asdict(s) for s in summaries]


def _parse_domain_wiki(data: dict, domain_name: str, known_ids: set[str]) -> WikiCompilation:
    """Parse the JSON output of a domain compilation call into a WikiCompilation.

    Enforces article ID uniqueness: if an ID collides with known_ids, it appends
    -{domain_slug} to make it unique.
    """
    domain_slug = slugify(domain_name)

    def _unique_id(art_id: str) -> str:
        if art_id not in known_ids:
            known_ids.add(art_id)
            return art_id
        new_id = f"{art_id}-{domain_slug}"
        known_ids.add(new_id)
        return new_id

    subtopics = [
        Subtopic(name=st["name"], article_ids=[_unique_id(aid) for aid in st.get("article_ids", [])])
        for st in data.get("subtopics", [])
    ]
    domains = [Domain(name=data.get("domain", domain_name), subtopics=subtopics)]

    # Build article ID remapping for subtopics that were changed
    orig_to_new: dict[str, str] = {}
    for st_orig, st_new in zip(data.get("subtopics", []), subtopics):
        for orig_id, new_id in zip(st_orig.get("article_ids", []), st_new.article_ids):
            orig_to_new[orig_id] = new_id

    articles = []
    for a in data.get("articles", []):
        art_id = orig_to_new.get(a["id"], _unique_id(a["id"]))
        articles.append(Article(
            id=art_id,
            title=a["title"],
            sources=[ArticleSource(**s) for s in a.get("sources", [])],
            content=a.get("content", ""),
            concepts=a.get("concepts", []),
            backlinks=a.get("backlinks", []),
        ))

    insights = [
        Insight(text=ins["text"], sources=ins.get("sources", []))
        for ins in data.get("insights", [])
    ]
    gaps = [
        Gap(gap=g["gap"], detail=g.get("detail", ""))
        for g in data.get("suggested_gaps", [])
    ]

    return WikiCompilation(
        title=domain_name,
        domain_name=domain_name,
        domains=domains,
        articles=articles,
        cross_topic_concepts=[],
        insights=insights,
        suggested_gaps=gaps,
    )


def _call_compile_domain(
    summaries: list[SourceSummary],
    domain_name: str,
    client: anthropic.Anthropic,
    model: str,
    known_ids: set[str],
) -> WikiCompilation:
    summaries_json = json.dumps(_summaries_to_dict(summaries), ensure_ascii=False, indent=2)
    user_msg = COMPILE_USER.format(domain_name=domain_name, summaries_json=summaries_json)
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=COMPILE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    return _parse_domain_wiki(data, domain_name, known_ids)


def _merge_wikis(wikis: list[WikiCompilation]) -> WikiCompilation:
    """Merge multiple WikiCompilation objects (from chunked compilation of one domain)."""
    if len(wikis) == 1:
        return wikis[0]

    all_articles: list[Article] = []
    all_domains: list[Domain] = []
    all_insights: list[Insight] = []
    all_gaps: list[Gap] = []
    seen_article_ids: set[str] = set()

    for w in wikis:
        for art in w.articles:
            if art.id not in seen_article_ids:
                all_articles.append(art)
                seen_article_ids.add(art.id)
        all_domains.extend(w.domains)
        all_insights.extend(w.insights)
        all_gaps.extend(w.suggested_gaps)

    return WikiCompilation(
        title=wikis[0].title,
        domain_name=wikis[0].domain_name,
        domains=all_domains,
        articles=all_articles,
        cross_topic_concepts=[],
        insights=all_insights,
        suggested_gaps=all_gaps,
    )


def compile_wiki_domain(
    summaries: list[SourceSummary],
    domain_name: str,
    client: anthropic.Anthropic,
    model: str,
    known_ids: set[str] | None = None,
    progress_cb: Callable[[str], None] | None = None,
) -> WikiCompilation:
    """Compile summaries for one Deep Domain into wiki articles. Chunks if too large.

    Args:
        known_ids: Set of already-used article IDs across all domains.
                   Mutated in-place to register newly created IDs.
    """
    if known_ids is None:
        known_ids = set()

    total_chars = sum(len(json.dumps(dataclasses.asdict(s))) for s in summaries)

    if total_chars <= CHUNK_THRESHOLD_CHARS:
        if progress_cb:
            progress_cb(f"Compiling {len(summaries)} summaries for '{domain_name}'...")
        return _call_compile_domain(summaries, domain_name, client, model, known_ids)

    if progress_cb:
        progress_cb(f"Large domain '{domain_name}' ({len(summaries)} summaries) — compiling in chunks...")
    chunk_size = max(5, len(summaries) // ((total_chars // CHUNK_THRESHOLD_CHARS) + 1))
    chunks = [summaries[i:i + chunk_size] for i in range(0, len(summaries), chunk_size)]
    wikis = []
    for idx, chunk in enumerate(chunks):
        if progress_cb:
            progress_cb(f"  Chunk {idx+1}/{len(chunks)} ({len(chunk)} summaries)...")
        wikis.append(_call_compile_domain(chunk, domain_name, client, model, known_ids))
    return _merge_wikis(wikis)


# Keep old name as alias for backwards compat with incremental path in cli.py
def compile_wiki(
    summaries: list[SourceSummary],
    client: anthropic.Anthropic,
    model: str,
    progress_cb: Callable[[str], None] | None = None,
) -> WikiCompilation:
    """Legacy single-pass compile (used by --incremental path). Compiles all summaries as one domain."""
    return compile_wiki_domain(summaries, "Knowledge Base", client, model, set(), progress_cb)


def compile_active_topic(
    summaries: list[SourceSummary],
    topic_name: str,
    client: anthropic.Anthropic,
    model: str,
) -> ActiveNote:
    """Compile summaries for one Active Topic into a single synthesized note."""
    summaries_json = json.dumps(_summaries_to_dict(summaries), ensure_ascii=False, indent=2)
    user_msg = ACTIVE_COMPILE_USER.format(topic_name=topic_name, summaries_json=summaries_json)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=ACTIVE_COMPILE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)

    # Collect sources from all input summaries
    sources = [
        ArticleSource(platform=s.platform, title=s.title, date=s.date)
        for s in summaries
    ]
    return ActiveNote(
        topic=data.get("topic", topic_name),
        sources=sources,
        note=data.get("note", ""),
        concepts=data.get("concepts", []),
        related_domains=[],  # populated by compile_cross_domain
    )


def compile_cross_domain(
    lightweight_index: str,
    client: anthropic.Anthropic,
    model: str,
) -> dict:
    """Run a cross-domain analysis pass on a lightweight index string.

    Args:
        lightweight_index: A text string of <10K tokens containing article/note
            titles, one-line summaries, concept tags, and source platforms.
            Do NOT pass full article content — it will exceed context window at scale.

    Returns dict with keys:
        cross_topic_concepts: list of {concept, appears_in, note}
        insights: list of {text, sources}
        suggested_gaps: list of {gap, detail}
        active_topic_related_domains: {topic_slug: [domain_name, ...]}
    """
    user_msg = CROSS_DOMAIN_USER.format(lightweight_index=lightweight_index)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=CROSS_DOMAIN_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def compile_incremental(
    new_summary: SourceSummary,
    wiki_dir: Path,
    client: anthropic.Anthropic,
    model: str,
) -> dict:
    """Incrementally integrate one new source summary into the existing wiki."""
    index_path = wiki_dir / "index.md"
    if not index_path.exists():
        raise FileNotFoundError("No existing wiki index found. Run full compile first.")

    index_content = index_path.read_text(encoding="utf-8")
    new_summary_json = json.dumps(dataclasses.asdict(new_summary), ensure_ascii=False, indent=2)

    user_msg = INCREMENTAL_USER.format(
        index_content=index_content,
        new_summary_json=new_summary_json,
    )
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=INCREMENTAL_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
