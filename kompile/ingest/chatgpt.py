"""Parse ChatGPT JSON export.

Export format:
  ZIP containing conversations.json — an array of conversation objects.
  Each conversation: { title, create_time, mapping: { node_id: { message, children, parent } } }
  Each message node: { id, message: { author: {role}, content: {parts: [...]}, create_time } }
"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path

from kompile.models import Source


def _iso_date(ts: float | str | None) -> str:
    if ts is None:
        return ""
    try:
        dt = datetime.fromtimestamp(float(ts))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(ts)[:10]


def _extract_text(message: dict) -> str:
    content = message.get("content", {})
    if not content:
        return ""
    parts = content.get("parts", [])
    return "\n".join(str(p) for p in parts if isinstance(p, str) and p.strip())


def _linearize_mapping(mapping: dict) -> list[dict]:
    """Walk the message tree in order (root → leaf)."""
    # Find root: node whose parent is None or not in mapping
    root_id = None
    for node_id, node in mapping.items():
        if node.get("parent") is None or node["parent"] not in mapping:
            root_id = node_id
            break

    if root_id is None:
        return []

    messages = []
    stack = [root_id]
    visited = set()
    while stack:
        node_id = stack.pop(0)
        if node_id in visited:
            continue
        visited.add(node_id)
        node = mapping.get(node_id, {})
        msg = node.get("message")
        if msg:
            messages.append(msg)
        children = node.get("children", [])
        stack = children + stack  # prepend to maintain order
    return messages


def _parse_conversations(data: list[dict]) -> list[Source]:
    sources = []
    for conv in data:
        uid = conv.get("id", conv.get("conversation_id", ""))
        title = conv.get("title") or "Untitled conversation"
        date = _iso_date(conv.get("create_time"))
        mapping = conv.get("mapping", {})
        messages = _linearize_mapping(mapping)

        lines = []
        for msg in messages:
            role = msg.get("author", {}).get("role", "unknown")
            if role not in ("user", "assistant"):
                continue
            text = _extract_text(msg)
            if text.strip():
                label = "Human" if role == "user" else "Assistant"
                lines.append(f"{label}: {text.strip()}")

        content = "\n\n".join(lines)
        if not content.strip():
            continue

        sources.append(Source(
            id=f"chatgpt_{uid}" if uid else f"chatgpt_{len(sources)}",
            platform="chatgpt",
            title=title,
            date=date,
            content=content,
            metadata={"message_count": len(lines)},
        ))
    return sources


def parse_chatgpt_export(path: str | Path) -> list[Source]:
    """Parse a ChatGPT export. Accepts a ZIP or the conversations.json file directly."""
    p = Path(path)
    sources: list[Source] = []

    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as zf:
            for name in zf.namelist():
                if name.endswith("conversations.json") or (name.endswith(".json") and "conversation" in name.lower()):
                    with zf.open(name) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            sources.extend(_parse_conversations(data))
                            break
    elif p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            sources.extend(_parse_conversations(data))

    return sources
