from app.config import config
from langchain.vectorstores import Chroma
from app.services.embeddings import get_embeddings

def get_vectorstore():
    embeddings=get_embeddings()
    return Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=embeddings
    )
    