import os
from youtube_transcript_api import YouTubeTranscriptApi
from app.storage.cache import save_transcript, load_transcript
from app.storage.vector_store import add_to_vectorstore

def get_transcript(video_id: str, video_url: str = None):
    """Fetch transcript by video ID, caching if available."""
    cached = load_transcript(video_id)
    if cached:
        return cached

    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_text = " ".join([entry['text'] for entry in transcript_data])
    save_transcript(video_id, transcript_text)
    return transcript_text

def process_video(video_id: str, video_url: str = None):
    """Fetch transcript, split it, and embed into vectorstore."""
    transcript = get_transcript(video_id, video_url)
    chunks = split_transcript(transcript)
    add_to_vectorstore(chunks)
    return "Transcript processed successfully."

def split_transcript(text: str, chunk_size: int = 1000):
    """Split long transcript into smaller chunks."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]



