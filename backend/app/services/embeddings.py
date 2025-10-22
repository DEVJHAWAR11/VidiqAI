from app.config import config
from langchain_huggingface import HuggingFaceEmbeddings

def get_embeddings():
    """Return embeddings model based on provider."""
    if config.LLM_PROVIDER == "groq":
        # Use free local embeddings (no API key needed)
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )