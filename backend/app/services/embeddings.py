from app.config import config
from langchain_openai import OpenAIEmbeddings
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
    else:  # openai
        return OpenAIEmbeddings(
            openai_api_key=config.OPENAI_API_KEY,
            model=config.OPENAI_EMBEDDING_MODEL
        )