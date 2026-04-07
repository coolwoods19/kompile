"""Persist pipeline state between runs (ingested sources, filter results, summaries)."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from kompile.models import FilterResult, SourceSummary, Claim


_STATE_FILE = ".kompile_state.json"


def _default_state() -> dict:
    return {
        "sources": {},            # id → {id, platform, title, date, metadata, content_hash}
        "filter_results": {},     # id → {source_id, keep, topics, summary}
        "summaries": {},          # id → SourceSummary as dict
        "tier_classifications": {},  # topic → {sources: [...], tier: "deep"|"active"|"surface"}
    }


def load_state(root: Path) -> dict:
    p = root / _STATE_FILE
    if p.exists():
        state = json.loads(p.read_text(encoding="utf-8"))
        # Backfill key for states written before tier_classifications was added
        if "tier_classifications" not in state:
            state["tier_classifications"] = {}
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


def state_unfiltered_source_ids(state: dict) -> set[str]:
    return set(state["sources"].keys()) - set(state["filter_results"].keys())


def state_unsummarized_kept_ids(state: dict) -> set[str]:
    kept = {sid for sid, r in state["filter_results"].items() if r.get("keep")}
    return kept - set(state["summaries"].keys())
