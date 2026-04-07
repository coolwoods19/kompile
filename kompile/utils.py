"""Shared utilities for KOMPILE."""
from __future__ import annotations

import hashlib
import re
import unicodedata


def slugify(name: str) -> str:
    """Convert a name to a URL/filesystem-safe slug.

    Handles:
    - ASCII: lowercase, spaces → hyphens, strip special chars
    - Chinese characters: convert to pinyin via pypinyin if available,
      fallback to a short MD5 hash prefix to avoid path collisions
    - Any other unicode: NFKD-normalize then drop non-ASCII

    Examples:
        "AI Infrastructure"  → "ai-infrastructure"
        "AI基础设施"          → "ai-ji-chu-she-shi"  (or "ai-a3f2b1" on fallback)
        "Groq / LPU"         → "groq-lpu"
    """
    if not name:
        return "unnamed"

    # Split into ASCII and non-ASCII parts to handle mixed strings
    result_parts: list[str] = []
    current_ascii = ""

    i = 0
    while i < len(name):
        ch = name[i]
        cp = ord(ch)
        # CJK Unified Ideographs (and extensions) + Katakana + Hiragana + Hangul
        if (0x4E00 <= cp <= 0x9FFF or   # CJK main block
                0x3400 <= cp <= 0x4DBF or   # CJK extension A
                0x20000 <= cp <= 0x2A6DF or  # CJK extension B
                0x3040 <= cp <= 0x30FF or   # Hiragana + Katakana
                0xAC00 <= cp <= 0xD7AF):    # Hangul syllables
            # Flush ASCII buffer
            if current_ascii:
                result_parts.append(current_ascii)
                current_ascii = ""
            # Convert CJK via pypinyin or hash fallback
            result_parts.append(_cjk_to_slug(ch))
        else:
            current_ascii += ch
        i += 1

    if current_ascii:
        result_parts.append(current_ascii)

    combined = "-".join(p.strip() for p in result_parts if p.strip())

    # NFKD-normalize + drop non-ASCII from the combined result
    combined = unicodedata.normalize("NFKD", combined)
    combined = combined.encode("ascii", "ignore").decode("ascii")

    # Lowercase, replace non-alphanumeric runs with hyphens
    combined = combined.lower()
    combined = re.sub(r"[^a-z0-9]+", "-", combined)
    combined = combined.strip("-")

    if not combined:
        # Ultimate fallback: hash of original name
        return "topic-" + hashlib.md5(name.encode("utf-8")).hexdigest()[:8]

    return combined


def _cjk_to_slug(char: str) -> str:
    """Convert a single CJK character to a pinyin slug or hash fallback."""
    try:
        from pypinyin import pinyin, Style
        result = pinyin(char, style=Style.NORMAL)
        if result and result[0]:
            return result[0][0]
    except ImportError:
        pass
    # Hash fallback: 4-char hex per CJK character — still readable and collision-safe
    return hashlib.md5(char.encode("utf-8")).hexdigest()[:4]
