from app.config import config
from app.services.embeddings import get_embeddings
from app.services.qa_chain import create_qa_chain
from storage.vector_store import get_vectorstore
from langchain.chat_models import openai

llm=openai(openai_api_key=config.OPENAI_API_KEY,temperature=0)

vectorstore=get_vectorstore()

qa_chain=create_qa_chain(llm,vectorstore)

