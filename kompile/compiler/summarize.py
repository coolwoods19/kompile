"""Summarize kept sources using Sonnet — extract claims, frameworks, key terms."""
from __future__ import annotations

import json
from typing import Callable

import anthropic

from kompile.models import Claim, FilterResult, Source, SourceSummary
from .prompts import SUMMARIZE_SYSTEM, SUMMARIZE_USER

MAX_CONTENT_CHARS = 160_000  # ~40K tokens, within Sonnet's 200K window at 50% limit


def summarize_source(
    source: Source,
    client: anthropic.Anthropic,
    model: str,
) -> SourceSummary:
    content = source.content[:MAX_CONTENT_CHARS]
    user_msg = SUMMARIZE_USER.format(
        platform=source.platform,
        title=source.title,
        date=source.date,
        content=content,
    )
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SUMMARIZE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)

    claims = [
        Claim(
            text=c["text"],
            type=c.get("type", "fact"),
            confidence=c.get("confidence", "stated"),
        )
        for c in data.get("claims", [])
    ]

    return SourceSummary(
        source_id=source.id,
        platform=source.platform,
        title=source.title,
        date=source.date,
        claims=claims,
        frameworks=data.get("frameworks", []),
        key_terms=data.get("key_terms", []),
    )


def summarize_sources(
    sources: list[Source],
    filter_results: list[FilterResult],
    client: anthropic.Anthropic,
    model: str,
    progress_cb: Callable[[int, int, SourceSummary], None] | None = None,
) -> list[SourceSummary]:
    kept_ids = {r.source_id for r in filter_results if r.keep}
    kept = [s for s in sources if s.id in kept_ids]
    summaries = []
    for i, source in enumerate(kept):
        summary = summarize_source(source, client, model)
        summaries.append(summary)
        if progress_cb:
            progress_cb(i + 1, len(kept), summary)
    return summaries
