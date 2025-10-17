from fastapi import APIRouter, HTTPException, status
from app.api.auth import verify_api_key
from app.models.schemas import (
    ProcessVideoRequest, ProcessVideoResponse,
    AskQuestionRequest, AskQuestionResponse,
    SummaryRequest, SummaryResponse,
    ErrorResponse
)
from app.services.video_utils import extract_video_id, is_valid_video_id
from app.services.transcripts import process_video, TranscriptError
from app.api.deps import qa_chain
from app.storage.vector_store import load_vectorstore_for_video
from app.services.qa_chain import create_qa_chain
from app.api.deps import llm
router = APIRouter()

# Add to imports at top of endpoints.py
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ============ HEALTH CHECK ============
@router.get('/health')
def get_health():
    """Simple health check to ensure API is running"""
    return {"status": "ok", "message": "VidIQAI is running"}

from app.storage.cache import load_transcript
from app.services.transcripts import download_audio
import os

router = APIRouter()

@router.get('/check/{video_id}')
def check_transcript_status(video_id: str):
    """
    Check transcript status for a YouTube video.
    Returns: {status: "available" | "fetching" | "unavailable"}
    """
    # Check if transcript is cached
    transcript = load_transcript(video_id)
    if transcript:
        return {"status": "available"}

    # Check if audio is being downloaded (optional: check for temp file)
    audio_path = f"./data/audio/{video_id}.mp3"
    if os.path.exists(audio_path):
        return {"status": "fetching"}

    # Otherwise, transcript is not available
    return {"status": "unavailable"}


# ============ VIDEO PROCESSING ============
@router.post('/process', response_model=ProcessVideoResponse, status_code=status.HTTP_200_OK)
def process_video_endpoint(request: ProcessVideoRequest):
    """
    Process a YouTube video:
    1. Extract video ID from URL
    2. Fetch transcript
    3. Chunk and embed into vector store
    
    This MUST be called before /ask or /summary endpoints.
    """
    try:
        # Extract video ID from URL or use as-is
        video_id = extract_video_id(request.video_url)
        
        if not video_id or not is_valid_video_id(video_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL or video ID format"
            )
        
        # Process the video
        result = process_video(video_id, request.video_url)
        
        return ProcessVideoResponse(
            status="success",
            video_id=result["video_id"],
            video_url=result["video_url"],
            message=f"Video processed successfully. Created {result['chunks_created']} chunks.",
            chunks_created=result["chunks_created"],
            transcript_length=result["transcript_length"]
        )
        
    except TranscriptError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing video: {str(e)}"
        )

# ============ ASK QUESTION ============
@router.post('/ask', response_model=AskQuestionResponse)
def ask_question(request: AskQuestionRequest):
    """
    Ask a question about a processed video.
    
    NOTE: You must call /process first with the video URL!
    """
    try:
        # Validate video ID format
        if not is_valid_video_id(request.video_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video ID format"
            )
        
        # Create prompt for QA chain
        prompt = f"Video ID: {request.video_id}\nQuestion: {request.question}"
        
        # Get answer from QA chain
        result = qa_chain({"query": prompt})
        answer = result.get("result", "No answer found")
        source_docs = result.get("source_documents", [])
        
        return AskQuestionResponse(
            answer=answer,
            video_id=request.video_id,
            question=request.question,
            sources_used=len(source_docs)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error answering question: {str(e)}"
        )

# ============ VIDEO SUMMARY ============
@router.post('/summary', response_model=SummaryResponse)
def generate_summary(request: SummaryRequest):
    """
    Generate a comprehensive summary of a processed video.
    Retrieves content from video-specific vectorstore.
    """
    try:
        # 1. Validate the video ID format
        if not is_valid_video_id(request.video_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video ID format"
            )
        
        # 2. Load the vectorstore for this specific video_id
        try:
            vectorstore = load_vectorstore_for_video(request.video_id)
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video not processed yet. Please call /process endpoint first. Error: {str(e)}"
            )
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load video data: {str(e)}"
            )
        
        # 3. Create a QA chain for this video's vectorstore
        video_qa_chain = create_qa_chain(llm, vectorstore)
        
        # 4. Construct an improved summarization prompt
        prompt = (
            f"Based on the transcript of YouTube video ID: {request.video_id}, "
            "provide a comprehensive and well-structured summary that includes:\n"
            "1. Main topic and purpose of the video\n"
            "2. Key points and important topics discussed\n"
            "3. Notable insights or conclusions\n\n"
            "Write the summary in clear, concise language suitable for someone who hasn't watched the video."
        )
        
        # 5. Run the QA chain to generate summary
        result = video_qa_chain({"query": prompt})
        summary = result.get("result", "Could not generate summary.")
        
        # 6. Get actual transcript length from source documents
        source_docs = result.get("source_documents", [])
        total_transcript_length = sum(len(doc.page_content) for doc in source_docs)
        
        return SummaryResponse(
            summary=summary,
            video_id=request.video_id,
            transcript_length=total_transcript_length if total_transcript_length > 0 else len(summary)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in summary endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )


# ============ STATUS CHECK ============
@router.get("/status")
def get_status():
    """Show API metadata and system status"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "endpoints": ["/health", "/process", "/ask", "/summary", "/status"]
    }
    
    
from app.database.db import get_conversation_history, clear_session
from fastapi import Depends

@router.get('/history/{session_id}')
def get_history(session_id: str, api_key: str = Depends(verify_api_key)):
    return get_conversation_history(session_id)

@router.delete('/history/{session_id}')
def delete_history(session_id: str, api_key: str = Depends(verify_api_key)):
    clear_session(session_id)
    return {"message": f"History cleared for session {session_id}"}

from app.storage.vector_store import clear_vectorstore

@router.get('/dev/clear')
def clear_store():
    """Development endpoint to clear the global vectorstore (legacy)."""
    clear_vectorstore()
    return {"message": "Global vectorstore cleared."}


from fastapi import Depends

@router.get("/protected")
def protected_route(api_key: str = Depends(verify_api_key)):
    if api_key:
        return {"message": "You have access with a valid API key!"}
    else:
        return {"message": "You have access as a guest user."}


from fastapi import Request
from fastapi.responses import StreamingResponse
from app.storage.vector_store import load_vectorstore_for_video
import asyncio

@router.post('/ask/stream')
async def ask_question_stream(request: Request):
    """
    Stream LLM response for a question about a processed video.
    """
    data = await request.json()
    video_id = data.get("video_id")
    question = data.get("question")

    if not video_id or not question:
        return StreamingResponse(iter(["data: Error: Missing video_id or question\n\n"]), media_type="text/event-stream")

    # Load vectorstore and create QA chain
    vectorstore = load_vectorstore_for_video(video_id)
    qa_chain = create_qa_chain(llm, vectorstore)

    # Streaming generator
    async def event_stream():
        # Use LangChain streaming callback (pseudo-code, adapt to your LLM)
        buffer = ""
        for chunk in qa_chain.stream({"query": question}):  # .stream() must yield tokens/chunks
            buffer += chunk
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.01)  # Prevents blocking

        # Optionally, send final message
        yield f"data: [END]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
