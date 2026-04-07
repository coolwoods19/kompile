"""Depth classification: group filtered sources by topic and assign tiers.

Tiers:
  deep    — 5+ sources on a topic → full article compilation
  active  — 2-4 sources          → single synthesized note
  surface — 1 source             → archived with Haiku summary only, no compilation
"""
from __future__ import annotations

from collections import defaultdict

DEEP_THRESHOLD = 5
ACTIVE_THRESHOLD = 2  # 2-4 sources


def classify_topics(filter_results: dict) -> dict[str, dict]:
    """Group kept sources by topic and classify each topic into a tier.

    Args:
        filter_results: state["filter_results"] dict —
            {source_id: {keep: bool, topics: [str, ...], summary: str, ...}}

    Returns:
        {topic_name: {"sources": [source_id, ...], "tier": "deep"|"active"|"surface"}}
    """
    topic_to_sources: dict[str, list[str]] = defaultdict(list)

    for source_id, result in filter_results.items():
        if not result.get("keep"):
            continue
        topics = result.get("topics", [])
        if not topics:
            topics = ["Uncategorised"]
        for topic in topics:
            topic_to_sources[topic.strip()].append(source_id)

    classifications: dict[str, dict] = {}
    for topic, source_ids in topic_to_sources.items():
        count = len(source_ids)
        if count >= DEEP_THRESHOLD:
            tier = "deep"
        elif count >= ACTIVE_THRESHOLD:
            tier = "active"
        else:
            tier = "surface"
        classifications[topic] = {
            "sources": source_ids,
            "tier": tier,
        }

    return classifications
