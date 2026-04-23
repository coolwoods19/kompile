"""Persist pipeline state between runs (ingested sources, filter results, summaries)."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from kompile.models import (
    ActiveNote, ArticleSource, Claim, FilterResult, SourceSummary,
    WikiCompilation, Domain, Subtopic, Article, Concept, Insight, Gap,
)


_STATE_FILE = ".kompile_state.json"


def _default_state() -> dict:
    return {
        "sources": {},            # id → {id, platform, title, date, metadata, content_hash}
        "filter_results": {},     # id → {source_id, keep, topics, summary}
        "summaries": {},          # id → SourceSummary as dict
        "tier_classifications": {},  # topic → {sources: [...], tier: "deep"|"active"|"surface"}
        "compiled_domains": {},   # topic → WikiCompilation as dict
        "compiled_active_topics": {},  # topic → ActiveNote as dict
    }


def load_state(root: Path) -> dict:
    p = root / _STATE_FILE
    if p.exists():
        state = json.loads(p.read_text(encoding="utf-8"))
        if "tier_classifications" not in state:
            state["tier_classifications"] = {}
        if "compiled_domains" not in state:
            state["compiled_domains"] = {}
        if "compiled_active_topics" not in state:
            state["compiled_active_topics"] = {}
        return state
    return _default_state()


def save_state(root: Path, state: dict) -> None:
    p = root / _STATE_FILE
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def state_add_sources(state: dict, sources: list) -> None:
    import hashlib
    for s in sources:
        state["sources"][s.id] = {
            "id": s.id,
            "platform": s.platform,
            "title": s.title,
            "date": s.date,
            "metadata": s.metadata,
            "content_hash": hashlib.md5(s.content.encode()).hexdigest(),
        }


def state_add_filter_results(state: dict, results: list[FilterResult]) -> None:
    for r in results:
        state["filter_results"][r.source_id] = dataclasses.asdict(r)


def state_add_summaries(state: dict, summaries: list[SourceSummary]) -> None:
    for s in summaries:
        state["summaries"][s.source_id] = dataclasses.asdict(s)


def state_get_summaries(state: dict) -> list[SourceSummary]:
    summaries = []
    for data in state["summaries"].values():
        claims = [Claim(**c) for c in data.get("claims", [])]
        summaries.append(SourceSummary(
            source_id=data["source_id"],
            platform=data["platform"],
            title=data["title"],
            date=data["date"],
            claims=claims,
            frameworks=data.get("frameworks", []),
            key_terms=data.get("key_terms", []),
        ))
    return summaries


def state_add_tier_classifications(state: dict, classifications: dict) -> None:
    """Store topic tier classifications.

    Args:
        classifications: {topic_name: {"sources": [sid, ...], "tier": "deep"|"active"|"surface"}}
    """
    state["tier_classifications"] = classifications


def state_get_tier_classifications(state: dict) -> dict:
    """Return stored tier classifications."""
    return state.get("tier_classifications", {})


def state_add_compiled_domain(state: dict, topic: str, wiki: WikiCompilation) -> None:
    state.setdefault("compiled_domains", {})[topic] = dataclasses.asdict(wiki)


def state_add_compiled_active(state: dict, topic: str, note: ActiveNote) -> None:
    state.setdefault("compiled_active_topics", {})[topic] = dataclasses.asdict(note)


def state_get_compiled_domains(state: dict) -> dict[str, WikiCompilation]:
    result = {}
    for topic, d in state.get("compiled_domains", {}).items():
        articles = [
            Article(
                id=a["id"], title=a["title"], content=a["content"],
                concepts=a.get("concepts", []), backlinks=a.get("backlinks", []),
                sources=[ArticleSource(**s) for s in a.get("sources", [])],
            )
            for a in d.get("articles", [])
        ]
        domains = [
            Domain(name=dom["name"], subtopics=[Subtopic(**st) for st in dom.get("subtopics", [])])
            for dom in d.get("domains", [])
        ]
        result[topic] = WikiCompilation(
            title=d.get("title", topic),
            domain_name=d.get("domain_name", topic),
            domains=domains,
            articles=articles,
            cross_topic_concepts=[Concept(**c) for c in d.get("cross_topic_concepts", [])],
            insights=[Insight(**i) for i in d.get("insights", [])],
            suggested_gaps=[Gap(**g) for g in d.get("suggested_gaps", [])],
        )
    return result


def state_get_compiled_active_topics(state: dict) -> dict[str, ActiveNote]:
    result = {}
    for topic, d in state.get("compiled_active_topics", {}).items():
        result[topic] = ActiveNote(
            topic=d["topic"],
            sources=[ArticleSource(**s) for s in d.get("sources", [])],
            note=d.get("note", ""),
            concepts=d.get("concepts", []),
            related_domains=d.get("related_domains", []),
        )
    return result


def state_clear_compiled(state: dict) -> None:
    """Clear compile-stage checkpoints (call before a fresh full compile)."""
    state["compiled_domains"] = {}
    state["compiled_active_topics"] = {}


def state_unfiltered_source_ids(state: dict) -> set[str]:
    return set(state["sources"].keys()) - set(state["filter_results"].keys())


def state_unsummarized_kept_ids(state: dict) -> set[str]:
    kept = {sid for sid, r in state["filter_results"].items() if r.get("keep")}
    return kept - set(state["summaries"].keys())
