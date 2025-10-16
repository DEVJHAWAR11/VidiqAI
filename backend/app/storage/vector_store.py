from langchain_community.vectorstores import FAISS
from app.services.embeddings import get_embeddings
from app.config import config
import os

# Initialize embeddings once
_embeddings = get_embeddings()

# FAISS vector store path
FAISS_INDEX_PATH = config.CHROMA_DB_PATH.replace("chroma", "faiss")
os.makedirs(FAISS_INDEX_PATH, exist_ok=True)

# Global vectorstore instance
_vectorstore = None

def get_vectorstore():
    """Return FAISS vectorstore instance."""
    global _vectorstore
    
    if _vectorstore is None:
        index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
        
        # Load existing index if available
        if os.path.exists(index_file):
            try:
                _vectorstore = FAISS.load_local(
                    FAISS_INDEX_PATH, 
                    _embeddings,
                    allow_dangerous_deserialization=True  # Required for FAISS
                )
                print(f"✓ Loaded existing FAISS index from {FAISS_INDEX_PATH}")
            except Exception as e:
                print(f"⚠ Could not load existing index: {e}")
                # Create new empty index
                _vectorstore = FAISS.from_texts(["initialization"], _embeddings)
        else:
            # Create new empty index
            _vectorstore = FAISS.from_texts(["initialization"], _embeddings)
            print(f"✓ Created new FAISS index at {FAISS_INDEX_PATH}")
    
    return _vectorstore

def add_to_vectorstore(texts):
    """Add new text documents to vectorstore."""
    vectorstore = get_vectorstore()
    vectorstore.add_texts(texts)
    
    # Save to disk
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"✓ Added {len(texts)} texts to FAISS and saved to disk")

def clear_vectorstore():
    """Clear all stored data (for dev only)."""
    global _vectorstore
    
    # Delete index files
    index_file = os.path.join(FAISS_INDEX_PATH, "index.faiss")
    pkl_file = os.path.join(FAISS_INDEX_PATH, "index.pkl")
    
    if os.path.exists(index_file):
        os.remove(index_file)
    if os.path.exists(pkl_file):
        os.remove(pkl_file)
    
    # Reset global instance
    _vectorstore = None
    print("✓ Cleared FAISS vectorstore")
