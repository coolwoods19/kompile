"""Parse Claude.ai JSON export.

Export format (as of 2025):
  ZIP containing one or more JSON files, each an array of conversation objects.
  Each conversation: { uuid, name, created_at, updated_at, chat_messages: [...] }
  Each message: { uuid, sender ("human"|"assistant"), text, created_at, ... }
"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path

from kompile.models import Source


def _iso_date(ts: str | None) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ts[:10] if ts else ""


def _conversation_to_text(messages: list[dict]) -> str:
    lines = []
    for msg in messages:
        sender = msg.get("sender", "unknown").capitalize()
        # content may be in "text" or nested in "content" list
        text = msg.get("text", "")
        if not text:
            for part in msg.get("content", []):
                if isinstance(part, dict) and part.get("type") == "text":
                    text += part.get("text", "")
        if text:
            lines.append(f"{sender}: {text.strip()}")
    return "\n\n".join(lines)


def _parse_conversations(data: list[dict]) -> list[Source]:
    sources = []
    for conv in data:
        uid = conv.get("uuid", "")
        title = conv.get("name") or "Untitled conversation"
        date = _iso_date(conv.get("created_at", ""))
        messages = conv.get("chat_messages", [])
        content = _conversation_to_text(messages)
        if not content.strip():
            continue
        sources.append(Source(
            id=f"claude_{uid}",
            platform="claude",
            title=title,
            date=date,
            content=content,
            metadata={"uuid": uid, "message_count": len(messages)},
        ))
    return sources


def parse_claude_export(path: str | Path) -> list[Source]:
    """Parse a Claude.ai export. Accepts a ZIP file or a directory of JSON files."""
    p = Path(path)
    sources: list[Source] = []

    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as zf:
            for name in zf.namelist():
                if name.endswith(".json"):
                    with zf.open(name) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            sources.extend(_parse_conversations(data))
    elif p.is_dir():
        for json_file in sorted(p.glob("**/*.json")):
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                sources.extend(_parse_conversations(data))
    elif p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            sources.extend(_parse_conversations(data))

    return sources
