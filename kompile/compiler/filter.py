"""Filter sources using Haiku — keep/discard + topic tags + summary."""
from __future__ import annotations

from typing import Callable

import anthropic

from kompile.models import FilterResult, Source
from kompile.utils import parse_llm_json
from .prompts import FILTER_SYSTEM, FILTER_USER

# Haiku context window ~200K; hard limit at 50% = 100K tokens
# Average conversation ~5K tokens — well within window
MAX_CONTENT_CHARS = 80_000  # ~20K tokens, conservative


def filter_source(
    source: Source,
    client: anthropic.Anthropic,
    model: str,
) -> FilterResult:
    content = source.content[:MAX_CONTENT_CHARS]
    user_msg = FILTER_USER.format(
        platform=source.platform,
        title=source.title,
        date=source.date,
        content=content,
    )
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=FILTER_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    data = parse_llm_json(response.content[0].text)
    return FilterResult(
        source_id=source.id,
        keep=bool(data.get("keep", False)),
        topics=data.get("topics", []),
        summary=data.get("summary", ""),
    )


def filter_sources(
    sources: list[Source],
    client: anthropic.Anthropic,
    model: str,
    progress_cb: Callable[[int, int, FilterResult], None] | None = None,
) -> list[FilterResult]:
    results = []
    for i, source in enumerate(sources):
        result = filter_source(source, client, model)
        results.append(result)
        if progress_cb:
            progress_cb(i + 1, len(sources), result)
    return results
