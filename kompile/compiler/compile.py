"""Core compilation step: cross-source synthesis → wiki articles + knowledge map.

Two-pass strategy (as per product spec Section 4.6):
  Pass 1: per-source summaries (done in summarize.py, ~500 tokens each)
  Pass 2: feed ALL summaries into one Sonnet call → wiki JSON

If total summary tokens would exceed 80K chars (~20K tokens), chunk by topic and
compile each chunk, then merge.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Callable

import anthropic

from kompile.models import (
    Article, ArticleSource, Concept, Domain, Gap, Insight,
    SourceSummary, Subtopic, WikiCompilation,
)
from .prompts import (
    COMPILE_SYSTEM, COMPILE_USER,
    INCREMENTAL_SYSTEM, INCREMENTAL_USER,
)

# At 50% of Sonnet's 200K window; summaries are text, ~4 chars/token
CHUNK_THRESHOLD_CHARS = 320_000  # ~80K tokens input limit for summaries


def _summaries_to_dict(summaries: list[SourceSummary]) -> list[dict]:
    return [dataclasses.asdict(s) for s in summaries]


def _parse_wiki(data: dict) -> WikiCompilation:
    domains = [
        Domain(
            name=d["name"],
            subtopics=[Subtopic(name=st["name"], article_ids=st.get("article_ids", []))
                       for st in d.get("subtopics", [])],
        )
        for d in data.get("domains", [])
    ]
    articles = [
        Article(
            id=a["id"],
            title=a["title"],
            sources=[ArticleSource(**s) for s in a.get("sources", [])],
            content=a.get("content", ""),
            concepts=a.get("concepts", []),
            backlinks=a.get("backlinks", []),
        )
        for a in data.get("articles", [])
    ]
    cross_concepts = [
        Concept(name=c.get("concept", c.get("name", "")), appears_in=c.get("appears_in", []), note=c.get("note", ""))
        for c in data.get("cross_topic_concepts", [])
    ]
    insights = [
        Insight(text=ins["text"], sources=ins.get("sources", []))
        for ins in data.get("insights", [])
    ]
    gaps = [
        Gap(gap=g["gap"], detail=g.get("detail", ""))
        for g in data.get("suggested_gaps", [])
    ]
    return WikiCompilation(
        title=data.get("title", "Knowledge Base"),
        domains=domains,
        articles=articles,
        cross_topic_concepts=cross_concepts,
        insights=insights,
        suggested_gaps=gaps,
    )


def _call_compile(
    summaries: list[SourceSummary],
    client: anthropic.Anthropic,
    model: str,
) -> WikiCompilation:
    summaries_json = json.dumps(_summaries_to_dict(summaries), ensure_ascii=False, indent=2)
    user_msg = COMPILE_USER.format(summaries_json=summaries_json)
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
    return _parse_wiki(data)


def _merge_wikis(wikis: list[WikiCompilation]) -> WikiCompilation:
    """Merge multiple WikiCompilation objects (from chunked compilation)."""
    if len(wikis) == 1:
        return wikis[0]

    all_articles = []
    all_domains = []
    all_concepts = []
    all_insights = []
    all_gaps = []
    seen_article_ids: set[str] = set()

    for w in wikis:
        for art in w.articles:
            if art.id not in seen_article_ids:
                all_articles.append(art)
                seen_article_ids.add(art.id)
        all_domains.extend(w.domains)
        all_concepts.extend(w.cross_topic_concepts)
        all_insights.extend(w.insights)
        all_gaps.extend(w.suggested_gaps)

    return WikiCompilation(
        title=wikis[0].title,
        domains=all_domains,
        articles=all_articles,
        cross_topic_concepts=all_concepts,
        insights=all_insights,
        suggested_gaps=all_gaps,
    )


def compile_wiki(
    summaries: list[SourceSummary],
    client: anthropic.Anthropic,
    model: str,
    progress_cb: Callable[[str], None] | None = None,
) -> WikiCompilation:
    """Compile summaries into a wiki. Chunks if too large."""
    total_chars = sum(len(json.dumps(dataclasses.asdict(s))) for s in summaries)

    if total_chars <= CHUNK_THRESHOLD_CHARS:
        if progress_cb:
            progress_cb(f"Compiling {len(summaries)} summaries in single pass...")
        return _call_compile(summaries, client, model)

    # Chunk by topic (simple split into groups of ~10)
    if progress_cb:
        progress_cb(f"Large knowledge base ({len(summaries)} summaries) — compiling in chunks...")
    chunk_size = max(5, len(summaries) // ((total_chars // CHUNK_THRESHOLD_CHARS) + 1))
    chunks = [summaries[i:i + chunk_size] for i in range(0, len(summaries), chunk_size)]
    wikis = []
    for idx, chunk in enumerate(chunks):
        if progress_cb:
            progress_cb(f"  Chunk {idx+1}/{len(chunks)} ({len(chunk)} summaries)...")
        wikis.append(_call_compile(chunk, client, model))
    return _merge_wikis(wikis)


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
