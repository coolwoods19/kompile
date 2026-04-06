"""Parse Claude Code project files.

Reads CLAUDE.md and other .md files from a project directory.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from kompile.models import Source


def _file_date(p: Path) -> str:
    try:
        ts = p.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return ""


def parse_claude_code_directory(path: str | Path) -> list[Source]:
    """Parse a Claude Code project directory. Reads CLAUDE.md and .md/.txt files."""
    p = Path(path)
    sources: list[Source] = []

    if not p.is_dir():
        raise ValueError(f"Not a directory: {path}")

    # Prioritize CLAUDE.md, then other markdown files
    md_files: list[Path] = []
    claude_md = p / "CLAUDE.md"
    if claude_md.exists():
        md_files.append(claude_md)

    for f in sorted(p.rglob("*.md")):
        if f != claude_md and ".git" not in f.parts:
            md_files.append(f)

    for f in sorted(p.rglob("*.txt")):
        if ".git" not in f.parts:
            md_files.append(f)

    for f in md_files:
        content = f.read_text(encoding="utf-8", errors="replace").strip()
        if not content:
            continue
        rel = f.relative_to(p)
        title = f.stem if f.name != "CLAUDE.md" else f"CLAUDE.md — {p.name}"
        sources.append(Source(
            id=f"claude_code_{rel!s}".replace("/", "_").replace(".", "_"),
            platform="claude_code",
            title=title,
            date=_file_date(f),
            content=content,
            metadata={"file": str(rel), "project": p.name},
        ))

    return sources
