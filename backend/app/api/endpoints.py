from fastapi import APIRouter

router = APIRouter()     #needed for larger applications with much complexity instead of FASTAPI()

#health
@router.get('/health')
def get_health():
    
    """simple check to ensure the api is running or not
    """
    return {"status":"ok"}



#summary
from app.api.deps import qa_chain

@router.post('/summary')                   #user gives a video_url when it hits this endpoint
def give_summary(video_url : str):
    """
    Takes a YouTube video URL, fetches transcript, and returns a summary.
    """
    
    prompt=f'Summarize this Video {video_url}'
    
    summary = qa_chain.run(prompt)
    
    return {'Summary':summary}


@router.post('/ask')
def give_answer(video_url:str,question:str):
    """
    Take video URL and user question, return answer from QA chain.
    """
    # Combine video URL and user question in the prompt
    
    prompt=f"Video:{video_url}\nQuestion:{question}"
    
    answer=qa_chain.run(prompt)
    
    return {"Answer":answer}


@router.get("/status")
def get_status():
    """
    Optional endpoint to show metadata like number of videos processed.
    """
    return {
        "videos_processed": 12,
        "vectorstore_type": "Chroma",
        "LLM_provider": "OpenAI"
    }
    
    


    