import os
from youtube_transcript_api import YouTubeTranscriptApi
from app.storage.cache import save_transcript, load_transcript
from app.storage.vector_store import add_to_vectorstore
from app.services.processing import chunk_text, clean_text


class TranscriptError(Exception):
    """Custom exception for transcript errors"""
    pass


def get_transcript(video_id: str, video_url: str = None):
    """Fetch transcript by video ID, using cache if available."""
    # Check cache first
    cached = load_transcript(video_id)
    if cached:
        print(f"✓ Using cached transcript for: {video_id}")
        return cached
    
    try:
        # NEW API (v1.2.0+): Create instance and use .fetch()
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        
        # Convert to raw data (list of dicts)
        transcript_data = fetched_transcript.to_raw_data()
        
        # Extract text from transcript entries
        transcript_text = " ".join([entry['text'] for entry in transcript_data])
        
        # Save to cache
        save_transcript(video_id, transcript_text)
        print(f"✓ Downloaded and cached transcript for: {video_id}")
        
        return transcript_text
        
    except Exception as e:
        # Provide helpful error message
        raise TranscriptError(f"Could not fetch transcript for video {video_id}: {str(e)}")


def process_video(video_id: str, video_url: str = None) -> dict:
    """
    Complete processing pipeline:
    1. Get transcript (cached or fresh)
    2. Clean text
    3. Chunk into smaller pieces
    4. Embed and store in vector database
    """
    # Step 1: Get transcript
    transcript = get_transcript(video_id, video_url)
    
    # Step 2: Clean text
    cleaned = clean_text(transcript)
    
    # Step 3: Chunk into smaller pieces
    chunks = chunk_text(cleaned, chunk_size=500)
    
    # Step 4: Store in FAISS vector DB
    add_to_vectorstore(chunks)
    
    print(f"✓ Processed {len(chunks)} chunks into vector store")
    
    return {
        "video_id": video_id,
        "video_url": video_url or f"https://www.youtube.com/watch?v={video_id}",
        "transcript_length": len(transcript),
        "chunks_created": len(chunks),
        "status": "success"
    }


def split_transcript(text: str, chunk_size: int = 1000):
    """Split transcript into chunks"""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
