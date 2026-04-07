"""Ingest a YouTube URL → Source object via transcript.

Uses youtube-transcript-api to fetch captions/subtitles.
pip install youtube-transcript-api
"""
from __future__ import annotations

import hashlib
import re
from datetime import date

from kompile.models import Source


def _extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def parse_youtube_url(url: str) -> Source | None:
    """Fetch a YouTube transcript and return a Source, or None on failure."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("Error: youtube-transcript-api is not installed. Run: pip install youtube-transcript-api")
        return None

    video_id = _extract_video_id(url)
    if not video_id:
        print(f"Failed to fetch transcript for {url}: could not extract video ID")
        return None

    try:
        # v1.x API: instantiate then call fetch(); falls back to any language
        api = YouTubeTranscriptApi()
        try:
            fetched = api.fetch(video_id, languages=["en"])
        except Exception:
            fetched = api.fetch(video_id, languages=["en", "en-US", "en-GB", "zh", "zh-TW", "zh-CN"])
        full_text = " ".join(
            segment.text if hasattr(segment, "text") else segment.get("text", "")
            for segment in fetched
        )

        if not full_text.strip():
            print(f"Failed to fetch transcript for {url}: transcript is empty")
            return None

        # Try to get video title via trafilatura (best-effort)
        title = f"YouTube: {video_id}"
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                metadata = trafilatura.extract_metadata(downloaded)
                if metadata and metadata.title:
                    title = metadata.title
        except Exception:
            pass  # Title extraction is best-effort

        pub_date = date.today().isoformat()
        source_id = "youtube-" + hashlib.md5(url.encode()).hexdigest()[:12]

        return Source(
            id=source_id,
            platform="youtube",
            title=title,
            date=pub_date,
            content=f"Title: {title}\nURL: {url}\nDate: {pub_date}\n\nTranscript:\n{full_text}",
            url=url,
            metadata={"video_id": video_id, "url": url, "title": title},
        )

    except Exception as e:
        # Provide a user-friendly message for common failures
        err_str = str(e)
        if "no element found" in err_str.lower() or "NoTranscriptFound" in type(e).__name__:
            print(f"Failed to fetch transcript for {url}: video has no captions")
        elif "TranscriptsDisabled" in type(e).__name__:
            print(f"Failed to fetch transcript for {url}: transcripts are disabled for this video")
        else:
            print(f"Failed to fetch transcript for {url}: {e}")
        return None
