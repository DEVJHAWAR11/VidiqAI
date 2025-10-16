import os
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from app.storage.cache import save_transcript, load_transcript
from app.storage.vector_store import add_to_vectorstore
from app.services.processing import chunk_text, clean_text

class TranscriptError(Exception):
    """Custom exception for transcript-related errors"""
    pass

def get_transcript(video_id: str, video_url: str = None):
    """
    Fetch transcript by video ID, using cache if available.
    
    Args:
        video_id: YouTube video ID
        video_url: Optional full URL for reference
        
    Returns:
        Transcript text as string
        
    Raises:
        TranscriptError: If transcript unavailable or video doesn't exist
    """
    # Check cache first
    cached = load_transcript(video_id)
    if cached:
        print(f"✓ Loaded transcript from cache for video: {video_id}")
        return cached
    
    try:
        # Fetch from YouTube
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry['text'] for entry in transcript_data])
        
        # Save to cache
        save_transcript(video_id, transcript_text)
        print(f"✓ Fetched and cached transcript for video: {video_id}")
        
        return transcript_text
        
    except TranscriptsDisabled:
        raise TranscriptError(f"Transcripts are disabled for video: {video_id}")
    except NoTranscriptFound:
        raise TranscriptError(f"No transcript found for video: {video_id}")
    except Exception as e:
        raise TranscriptError(f"Error fetching transcript: {str(e)}")

def process_video(video_id: str, video_url: str = None) -> dict:
    """
    Complete video processing pipeline:
    1. Fetch transcript (from cache or YouTube)
    2. Clean and chunk the text
    3. Embed chunks into vector store
    
    Args:
        video_id: YouTube video ID
        video_url: Optional full URL
        
    Returns:
        Dictionary with processing stats
    """
    # Step 1: Get transcript
    transcript = get_transcript(video_id, video_url)
    
    # Step 2: Clean the transcript
    cleaned_transcript = clean_text(transcript)
    
    # Step 3: Chunk into smaller pieces
    chunks = chunk_text(cleaned_transcript, chunk_size=500)
    
    # Step 4: Add to vector store for retrieval
    add_to_vectorstore(chunks)
    
    print(f"✓ Processed {len(chunks)} chunks for video: {video_id}")
    
    return {
        "video_id": video_id,
        "video_url": video_url or f"https://www.youtube.com/watch?v={video_id}",
        "transcript_length": len(transcript),
        "chunks_created": len(chunks),
        "status": "success"
    }

def split_transcript(text: str, chunk_size: int = 1000):
    """Split long transcript into smaller chunks"""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]



