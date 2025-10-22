# app/services/qa_chain.py

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

def create_qa_chain(llm, vectorstore):
    # ENHANCED: Better prompt to prevent repetition
    prompt_template = """You are an AI assistant analyzing a YouTube video transcript. Use the context below to answer the question accurately and concisely.

Context from video transcript:
{context}

User Question: {question}

IMPORTANT INSTRUCTIONS:
1. Provide a clear, well-structured answer based ONLY on the transcript context
2. Write naturally without repeating words or phrases
3. Use proper formatting (bullet points, numbers) when appropriate
4. Be concise - avoid unnecessary elaboration
5. If the information is not in the transcript, say "This information is not covered in the video"
6. Do NOT duplicate or repeat sentences

Your Answer:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_kwargs={
                "k": 3,  # Retrieve top 3 most relevant chunks
                "fetch_k": 10  # Fetch more candidates for better filtering
            }
        ),
        return_source_documents=False,
        chain_type_kwargs={"prompt": PROMPT}
    )
