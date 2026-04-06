"""Parse raw text and markdown files."""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from kompile.models import Source


def _file_date(p: Path) -> str:
    try:
        ts = p.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return ""


def parse_raw_file(path: str | Path) -> Source:
    """Parse a single .md or .txt file as a raw manual source."""
    p = Path(path)
    content = p.read_text(encoding="utf-8", errors="replace").strip()
    uid = hashlib.md5(str(p.resolve()).encode()).hexdigest()[:8]
    return Source(
        id=f"manual_{uid}",
        platform="manual",
        title=p.stem,
        date=_file_date(p),
        content=content,
        metadata={"file": str(p)},
    )


def parse_raw_text(text: str, title: str = "Pasted text") -> Source:
    """Create a Source from pasted raw text."""
    uid = hashlib.md5(text[:200].encode()).hexdigest()[:8]
    today = datetime.now().strftime("%Y-%m-%d")
    return Source(
        id=f"manual_{uid}",
        platform="manual",
        title=title,
        date=today,
        content=text.strip(),
        metadata={},
    )
