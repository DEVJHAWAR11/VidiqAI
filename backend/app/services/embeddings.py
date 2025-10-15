from app.config import config
from langchain.embeddings.openai import OpenAIEmbeddings

def get_embeddings():
    return OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)
