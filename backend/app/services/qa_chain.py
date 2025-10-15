from langchain.chains import retrieval_qa

def create_qa_chain(llm,vectorstore):
    return retrieval_qa.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever()
    )