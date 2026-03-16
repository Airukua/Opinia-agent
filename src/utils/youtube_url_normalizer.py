from __future__ import annotations
from urllib.parse import parse_qs, urlparse
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_video_id(raw_input: str) -> str:
    """Extracts a YouTube video ID from URL or plain ID input.

    Supported inputs include:
    - Full watch URL, e.g. ``https://www.youtube.com/watch?v=...``
    - Short URL, e.g. ``https://youtu.be/...``
    - Shorts URL, e.g. ``https://www.youtube.com/shorts/...``
    - Plain video ID, e.g. ``YCLJz0TANaA``

    Args:
        raw_input: YouTube URL or direct video ID.

    Returns:
        Normalized video ID string.

    Raises:
        ValueError: If no valid video ID can be extracted.

    Example usage:
        >>> extract_video_id("https://www.youtube.com/watch?v=YCLJz0TANaA&list=abc")
        'YCLJz0TANaA'
    """
    candidate = (raw_input or "").strip()
    if not candidate:
        raise ValueError("Input is empty; expected YouTube URL or video ID")

    if "://" not in candidate and "/" not in candidate and "?" not in candidate:
        _validate_video_id(candidate)
        return candidate

    parsed = urlparse(candidate)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path or ""

    if "youtu.be" in hostname:
        video_id = path.strip("/").split("/")[0]
        _validate_video_id(video_id)
        return video_id

    if "youtube.com" in hostname or "youtube-nocookie.com" in hostname:
        query_v = parse_qs(parsed.query).get("v", [])
        if query_v:
            video_id = query_v[0]
            _validate_video_id(video_id)
            return video_id

        segments = [seg for seg in path.split("/") if seg]
        if len(segments) >= 2 and segments[0] in {"shorts", "embed", "v"}:
            video_id = segments[1]
            _validate_video_id(video_id)
            return video_id

    raise ValueError(f"Could not extract YouTube video ID from input: {raw_input}")


def _validate_video_id(video_id: str) -> None:
    """Validates minimal structure of a YouTube video ID."""
    cleaned = (video_id or "").strip()
    if not cleaned:
        raise ValueError("Extracted video ID is empty")
    if len(cleaned) < 6:
        raise ValueError(f"Extracted video ID looks invalid: {video_id}")
    logger.debug("Validated video_id=%s", cleaned)
