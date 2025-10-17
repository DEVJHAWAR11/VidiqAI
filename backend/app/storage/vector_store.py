from langchain_community.vectorstores import FAISS
from app.services.embeddings import get_embeddings
from app.config import config
import os

# Initialize embeddings once
_embeddings = get_embeddings()

# FAISS vector store base path
FAISS_BASE_PATH = config.CHROMA_DB_PATH.replace("chroma", "faiss")
os.makedirs(FAISS_BASE_PATH, exist_ok=True)

# Global vectorstore instance (for /ask endpoint backward compatibility)
_vectorstore = None

def get_vectorstore():
    """Return global FAISS vectorstore instance for legacy /ask endpoint."""
    global _vectorstore
    if _vectorstore is None:
        index_file = os.path.join(FAISS_BASE_PATH, "index.faiss")
        
        if os.path.exists(index_file):
            try:
                _vectorstore = FAISS.load_local(
                    FAISS_BASE_PATH,
                    _embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"✓ Loaded existing FAISS index from {FAISS_BASE_PATH}")
            except Exception as e:
                print(f"⚠ Could not load existing index: {e}")
                _vectorstore = FAISS.from_texts(["initialization"], _embeddings)
        else:
            _vectorstore = FAISS.from_texts(["initialization"], _embeddings)
            print(f"✓ Created new FAISS index at {FAISS_BASE_PATH}")
    
    return _vectorstore

def add_to_vectorstore(texts, video_id=None):
    """
    Add text documents to vectorstore.
    If video_id provided, saves to video-specific directory.
    Otherwise, adds to global vectorstore (legacy behavior).
    """
    if video_id:
        # Video-specific storage
        video_path = os.path.join(FAISS_BASE_PATH, video_id)
        os.makedirs(video_path, exist_ok=True)
        
        # Create new FAISS index for this video
        vectorstore = FAISS.from_texts(texts, _embeddings)
        vectorstore.save_local(video_path)
        print(f"✓ Added {len(texts)} texts to video-specific FAISS at {video_path}")
    else:
        # Legacy global storage
        vectorstore = get_vectorstore()
        vectorstore.add_texts(texts)
        vectorstore.save_local(FAISS_BASE_PATH)
        print(f"✓ Added {len(texts)} texts to global FAISS")

def load_vectorstore_for_video(video_id: str):
    """Load video-specific FAISS vectorstore."""
    video_path = os.path.join(FAISS_BASE_PATH, video_id)
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"No vectorstore found for video ID: {video_id}")
    
    index_file = os.path.join(video_path, "index.faiss")
    if not os.path.exists(index_file):
        raise FileNotFoundError(f"FAISS index file not found for video ID: {video_id}")
    
    try:
        vectorstore = FAISS.load_local(
            video_path,
            _embeddings,
            allow_dangerous_deserialization=True
        )
        print(f"✓ Loaded vectorstore for video {video_id}")
        return vectorstore
    except Exception as e:
        raise RuntimeError(f"Failed to load vectorstore for video {video_id}: {str(e)}")

def clear_vectorstore():
    """Clear all stored data (for dev only)."""
    global _vectorstore
    
    # Delete all FAISS files recursively
    import shutil
    if os.path.exists(FAISS_BASE_PATH):
        shutil.rmtree(FAISS_BASE_PATH)
        os.makedirs(FAISS_BASE_PATH, exist_ok=True)
    
    _vectorstore = None
    print("✓ Cleared all FAISS vectorstores")
