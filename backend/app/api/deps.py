from langchain_openai import ChatOpenAI  # Updated import for newer LangChain
from app.config import config
from app.storage.vector_store import get_vectorstore
from app.services.qa_chain import create_qa_chain

def get_llm():
    """Return OpenAI chat model with specified model."""
    return ChatOpenAI(
        openai_api_key=config.OPENAI_API_KEY,
        model_name=config.OPENAI_MODEL,  # Now uses config
        temperature=0,  # 0 = deterministic, 1 = creative
    )

# Initialize once when app starts
llm = get_llm()
vectorstore = get_vectorstore()
qa_chain = create_qa_chain(llm, vectorstore)
