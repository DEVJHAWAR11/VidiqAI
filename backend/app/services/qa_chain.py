# app/services/qa_chain.py

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

def create_qa_chain(llm, vectorstore):
    """
    Creates a LangChain RetrievalQA chain over a per-video FAISS vectorstore.

    Retrieval Strategy:
        - search_type: 'mmr' (Maximum Marginal Relevance)
          Ensures retrieved chunks are both relevant AND diverse,
          avoiding redundant context when multiple similar segments exist.
        - k=3: Return top 3 chunks for answer generation
        - fetch_k=10: Fetch 10 candidates before MMR re-ranking

    Prompt:
        Custom prompt enforces grounded, non-repetitive answers
        anchored strictly to the video transcript context.
    """
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
            search_type="mmr",       # Maximum Marginal Relevance for diverse retrieval
            search_kwargs={
                "k": 3,              # Return top 3 most relevant + diverse chunks
                "fetch_k": 10        # Fetch 10 candidates, MMR re-ranks to top 3
            }
        ),
        return_source_documents=False,
        chain_type_kwargs={"prompt": PROMPT}
    )
