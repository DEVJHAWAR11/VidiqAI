from langchain_groq import ChatGroq
from app.config import config
from app.storage.vector_store import get_vectorstore
from app.services.qa_chain import create_qa_chain

def get_llm():
    """Return LLM based on provider setting."""
    if config.LLM_PROVIDER == "groq":
        return ChatGroq(
            groq_api_key=config.GROQ_API_KEY,
            model_name=config.GROQ_MODEL,
            temperature=0.3,  # Lower temperature for more focused responses
            max_tokens=1024,
        )

# Initialize once when app starts
llm = get_llm()
vectorstore = get_vectorstore()
qa_chain = create_qa_chain(llm, vectorstore)