from __future__ import annotations

from typing import Optional
from urllib.parse import parse_qs, urlparse

YT_HOSTS = {"www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"}


def extract_video_id(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return parsed.path.lstrip("/") or None

    if parsed.path == "/watch":
        return parse_qs(parsed.query).get("v", [None])[0]

    if parsed.path.startswith("/shorts/"):
        parts = parsed.path.split("/")
        return parts[2] if len(parts) > 2 else None

    if parsed.path.startswith("/embed/"):
        parts = parsed.path.split("/")
        return parts[2] if len(parts) > 2 else None

    return None


def validate_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc not in YT_HOSTS:
        return False
    return extract_video_id(url) is not None
