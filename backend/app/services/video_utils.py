import re
from typing import Optional

def extract_video_id(video_input: str) -> Optional[str]:
    """
    Extract YouTube video ID from a URL or accept a direct video ID.
    """
    cleaned = video_input.strip()
    # 1. Already just a valid video ID?
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', cleaned):
        return cleaned

    # 2. Try to pull canonical ID from any supported format (robust)
    # Order matters: check for v= or /ID in any URL form
    patterns = [
        r"(?:v=|/)([A-Za-z0-9_-]{11})(?=\b|[&?/])",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned)
        if match:
            return match.group(1)

    return None

def is_valid_video_id(video_id: str) -> bool:
    return bool(re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id))