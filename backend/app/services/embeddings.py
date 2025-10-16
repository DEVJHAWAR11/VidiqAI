from app.config import config
from langchain_openai import OpenAIEmbeddings  # Updated import

def get_embeddings():
    """Return OpenAI embeddings model."""
    return OpenAIEmbeddings(
        openai_api_key=config.OPENAI_API_KEY,
        model=config.OPENAI_EMBEDDING_MODEL  # Now configurable
    )
