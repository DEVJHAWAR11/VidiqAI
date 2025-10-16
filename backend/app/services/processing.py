# app/services/processing.py

def clean_text(text: str) -> str:
    """
    Remove unnecessary line breaks and extra spaces.
    """
    return text.replace("\n", " ").strip()


def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """
    Split text into chunks of ~chunk_size words.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks
