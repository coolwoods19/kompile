"""Auto-detect input type and route to the correct parser.

Replaces the inline auto-detection block that was in cli.py.
"""
from __future__ import annotations

import zipfile
from pathlib import Path


def route_input(path_or_url: str) -> str:
    """Return the source type string for the given path or URL.

    Returns one of: "claude", "chatgpt", "claude_code", "youtube", "article", "raw"
    """
    s = path_or_url.strip()

    # YouTube first (before generic http check)
    if "youtube.com" in s or "youtu.be" in s:
        return "youtube"

    # Any other HTTP URL → article
    if s.startswith("http://") or s.startswith("https://"):
        return "article"

    p = Path(s)

    # ZIP file → peek inside to distinguish Claude vs ChatGPT
    if p.suffix.lower() == ".zip" and p.is_file():
        return _detect_zip_type(p)

    # Directory → Claude Code project
    if p.is_dir():
        return "claude_code"

    # Text/markdown files → raw
    if p.suffix.lower() in (".md", ".txt"):
        return "raw"

    # JSON file → try to detect type from filename or content
    if p.suffix.lower() == ".json":
        return _detect_json_type(p)

    # Default fallback
    return "raw"


def _detect_zip_type(path: Path) -> str:
    """Peek inside a ZIP to determine whether it's Claude or ChatGPT format."""
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            # ChatGPT export contains conversations.json at the root
            if any(n == "conversations.json" or n.endswith("/conversations.json") for n in names):
                return "chatgpt"
            # Claude export: JSON files that are arrays of conversations
            # Heuristic: check filename
            name_lower = path.name.lower()
            if "chatgpt" in name_lower or "gpt" in name_lower or "openai" in name_lower:
                return "chatgpt"
            return "claude"
    except Exception:
        return "claude"  # Default for unreadable ZIPs


def _detect_json_type(path: Path) -> str:
    """Peek at a standalone JSON file to determine its type."""
    name_lower = path.name.lower()
    if "chatgpt" in name_lower or "gpt" in name_lower or "openai" in name_lower:
        return "chatgpt"
    if "conversations" in name_lower:
        # Could be either; check content
        try:
            import json
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list) and data and "mapping" in data[0]:
                return "chatgpt"
        except Exception:
            pass
    return "claude"
