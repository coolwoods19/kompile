"""Ingest a web article URL → Source object.

Uses trafilatura to fetch and extract article body text.
pip install trafilatura
"""
from __future__ import annotations

import hashlib
from datetime import date

from kompile.models import Source


def parse_article_url(url: str) -> Source | None:
    """Fetch a web article and return a Source, or None on failure."""
    try:
        import trafilatura
    except ImportError:
        print("Error: trafilatura is not installed. Run: pip install trafilatura")
        return None

    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"Failed to fetch article at {url}: could not download page")
            return None

        text = trafilatura.extract(downloaded)
        if not text:
            print(f"Failed to fetch article at {url}: could not extract body text")
            return None

        # Extract metadata
        metadata = trafilatura.extract_metadata(downloaded)
        title = (metadata.title if metadata and metadata.title else None) or url
        pub_date = ""
        if metadata and metadata.date:
            pub_date = str(metadata.date)[:10]  # ISO date YYYY-MM-DD
        if not pub_date:
            pub_date = date.today().isoformat()

        source_id = "article-" + hashlib.md5(url.encode()).hexdigest()[:12]
        return Source(
            id=source_id,
            platform="article",
            title=title,
            date=pub_date,
            content=f"Title: {title}\nURL: {url}\nDate: {pub_date}\n\n{text}",
            url=url,
            metadata={"url": url, "title": title, "date": pub_date},
        )

    except Exception as e:
        print(f"Failed to fetch article at {url}: {e}")
        return None
