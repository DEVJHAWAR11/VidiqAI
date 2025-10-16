from langchain.chat_models import ChatOpenAI
from app.config import config
from app.storage.vector_store import get_vectorstore
from app.services.qa_chain import create_qa_chain

# Initialize core dependencies
def get_llm():
    """Return OpenAI chat model."""
    return ChatOpenAI(openai_api_key=config.OPENAI_API_KEY, temperature=0)

llm = get_llm()
vectorstore = get_vectorstore()
qa_chain = create_qa_chain(llm, vectorstore)

