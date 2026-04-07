"""Summarize kept sources using Sonnet — extract claims, frameworks, key terms."""
from __future__ import annotations

import time
from typing import Callable

import anthropic

from kompile.models import Claim, FilterResult, Source, SourceSummary
from kompile.utils import parse_llm_json
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
    for attempt in range(5):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=8096,
                system=SUMMARIZE_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            break
        except anthropic.RateLimitError:
            if attempt == 4:
                raise
            wait = 60 * (attempt + 1)
            print(f"    Rate limited — waiting {wait}s before retry...")
            time.sleep(wait)
    try:
        data = parse_llm_json(response.content[0].text)
    except Exception as e:
        print(f"    Warning: bad JSON for '{source.title[:60]}': {e}")
        return SourceSummary(
            source_id=source.id, platform=source.platform,
            title=source.title, date=source.date,
            claims=[], frameworks=[], key_terms=[],
        )

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
