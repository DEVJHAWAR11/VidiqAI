# app/services/processing.py
import re

def clean_text(text: str) -> str:
    """
    Clean transcript text by removing:
    - Timestamp markers like {ts:123}
    - Extra whitespace, line breaks
    - Special characters and formatting artifacts
    - Music/sound effect markers like [संगीत], [Music]
    """
    if not text:
        return ""
    
    # Remove timestamp markers: {ts:123}, {ts:0}, etc.
    text = re.sub(r'\{ts:\d+\}', '', text)
    
    # Remove sound effect markers: [संगीत], [Music], [Applause], etc.
    text = re.sub(r'\[.*?\]', '', text)
    
    # Remove parentheses with metadata: (music), (laughing), etc.
    text = re.sub(r'\(.*?\)', '', text)
    
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Replace multiple line breaks with space
    text = text.replace('\n', ' ')
    
    # Remove extra whitespace (multiple spaces to single space)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into chunks with overlap for better context preservation.
    
    Args:
        text: Cleaned text to chunk
        chunk_size: Number of words per chunk (default: 500)
        overlap: Number of overlapping words between chunks (default: 50)
    
    Returns:
        List of text chunks with overlap
    """
    if not text:
        return []
    
    words = text.split()
    
    # If text is smaller than chunk_size, return as single chunk
    if len(words) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(words):
        # Get chunk of words
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap
        
        # Prevent infinite loop if we're at the end
        if end >= len(words):
            break
    
    return chunks
