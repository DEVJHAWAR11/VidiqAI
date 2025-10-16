import os
from app.config import config

CACHE_DIR = config.CACHE_PATH
os.makedirs(CACHE_DIR, exist_ok=True)

def save_transcript(video_id: str, transcript: str):
    """Save transcript locally."""
    file_path = os.path.join(CACHE_DIR, f"{video_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(transcript)

def load_transcript(video_id: str) -> str | None:
    """Load transcript if it exists."""
    file_path = os.path.join(CACHE_DIR, f"{video_id}.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return None
