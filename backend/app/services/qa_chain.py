from langchain.chains import RetrievalQA

def create_qa_chain(llm, vectorstore):
    """Create a RetrievalQA chain using the given LLM and vectorstore."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain

