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


def classify_topics(
    filter_results: dict,
    client=None,
    model: str = "claude-haiku-4-5-20251001",
) -> dict[str, dict]:
    """Group kept sources by topic and classify each topic into a tier.

    If client is provided, runs an LLM normalization pass to merge similar/granular
    topics into broader categories before tiering.

    Args:
        filter_results: state["filter_results"] dict —
            {source_id: {keep: bool, topics: [str, ...], summary: str, ...}}
        client: optional anthropic.Anthropic instance for topic normalization
        model: model to use for normalization (Haiku is fine)

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

    # Normalize topics via LLM if client provided and there are many granular topics
    if client and len(topic_to_sources) > 10:
        topic_to_sources = _normalize_topics(topic_to_sources, client, model)

    classifications: dict[str, dict] = {}
    for topic, source_ids in topic_to_sources.items():
        # Deduplicate source IDs (a source may map to the same canonical topic multiple times)
        unique_ids = list(dict.fromkeys(source_ids))
        count = len(unique_ids)
        if count >= DEEP_THRESHOLD:
            tier = "deep"
        elif count >= ACTIVE_THRESHOLD:
            tier = "active"
        else:
            tier = "surface"
        classifications[topic] = {
            "sources": unique_ids,
            "tier": tier,
        }

    return classifications


_BATCH_SIZE = 80  # topics per LLM call — keeps response well under token limit


def _normalize_topics(
    topic_to_sources: dict[str, list[str]],
    client,
    model: str,
) -> dict[str, list[str]]:
    """Use an LLM to merge granular topics into broader canonical categories.

    Processes topics in batches to stay within output token limits.
    Returns a new topic_to_sources mapping with merged topics.
    """
    all_topics = list(topic_to_sources.keys())
    mapping: dict[str, str] = {}

    # First pass: determine canonical categories from first batch, reuse in subsequent batches
    # so all batches converge on the same category names.
    for i in range(0, len(all_topics), _BATCH_SIZE):
        batch = all_topics[i : i + _BATCH_SIZE]
        batch_mapping = _normalize_batch(batch, client, model)
        if batch_mapping is None:
            print(f"  Batch {i // _BATCH_SIZE + 1} normalization failed, keeping original topics for this batch.")
            batch_mapping = {t: t for t in batch}
        mapping.update(batch_mapping)

    # Build new mapping: canonical_topic → merged list of source IDs
    canonical: dict[str, list[str]] = defaultdict(list)
    for orig_topic, source_ids in topic_to_sources.items():
        canonical_topic = mapping.get(orig_topic, orig_topic)
        canonical[canonical_topic].extend(source_ids)

    return canonical


def _normalize_batch(topics: list[str], client, model: str) -> dict[str, str] | None:
    """Normalize one batch of topics. Returns mapping dict or None on failure.

    Uses pipe-delimited lines instead of JSON to avoid escaping issues with
    topic names that contain quotes or special characters.
    Format: original topic|Canonical Category
    """
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(topics))
    prompt = (
        "Group these granular topic tags into broader canonical categories "
        "for a personal knowledge base. Merge similar, overlapping, or overly-specific "
        "topics into broad categories.\n\n"
        "Rules:\n"
        "- Use 2-4 word category names (e.g. 'AI Infrastructure', 'Content Strategy', 'Personal Finance')\n"
        "- Every input topic must map to exactly one output category\n"
        "- Output one line per topic, format: ORIGINAL_TOPIC|Canonical Category\n"
        "- No extra text, no numbering, just the pipe-delimited lines\n\n"
        f"Topics:\n{numbered}"
    )
    try:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        mapping: dict[str, str] = {}
        for line in raw.splitlines():
            line = line.strip()
            if "|" not in line:
                continue
            orig, _, canonical = line.partition("|")
            orig = orig.strip()
            canonical = canonical.strip()
            if orig and canonical:
                mapping[orig] = canonical
        # Fallback for any topics the model missed
        for t in topics:
            if t not in mapping:
                mapping[t] = t
        return mapping
    except Exception as e:
        print(f"  Normalization batch failed: {e}")
        return None
