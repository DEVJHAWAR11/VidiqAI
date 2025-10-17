from langchain.chains import RetrievalQA
from langchain_core.vectorstores import VectorStoreRetriever

def create_qa_chain(llm, vectorstore):
    """Create a RetrievalQA chain using modern LangChain API."""
    retriever = VectorStoreRetriever(vectorstore=vectorstore, search_kwargs={"k": 5})
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )
    return qa_chain
