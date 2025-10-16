from langchain.vectorstores import Chroma
from app.services.embeddings import get_embeddings
from app.config import config

# Initialize embeddings and Chroma once
_embeddings = get_embeddings()
_vectorstore = Chroma(
    persist_directory=config.CHROMA_DB_PATH,
    embedding_function=_embeddings
)

def get_vectorstore():
    """Return global Chroma vectorstore instance."""
    return _vectorstore

def add_to_vectorstore(texts):
    """Add new text documents to vectorstore."""
    _vectorstore.add_texts(texts)
    _vectorstore.persist()

def clear_vectorstore():
    """Clear all stored data (for dev only)."""
    _vectorstore.delete_collection()
    _vectorstore.persist()
