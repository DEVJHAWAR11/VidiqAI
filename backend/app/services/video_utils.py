import re
from typing import Optional

def extract_video_id(video_input: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL or return as-is if already an ID.
    
    Handles formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - Just VIDEO_ID (11 characters)
    
    Args:
        video_input: YouTube URL or video ID
        
    Returns:
        Extracted video ID or None if invalid
    """
    # If it's already a video ID (11 alphanumeric characters and hyphens/underscores)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', video_input):
        return video_input
    
    # Pattern to extract video ID from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',  # Standard watch URL
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',              # Shortened URL
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',    # Embed URL
        r'(?:youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',        # Old-style URL
    ]
    
    for pattern in patterns:
        match = re.search(pattern, video_input)
        if match:
            return match.group(1)
    
    return None

def is_valid_video_id(video_id: str) -> bool:
    """Check if a string is a valid YouTube video ID format"""
    return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))
