from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    ProcessVideoRequest, ProcessVideoResponse,
    AskQuestionRequest, AskQuestionResponse,
    SummaryRequest, SummaryResponse,
    ErrorResponse
)
from app.services.video_utils import extract_video_id, is_valid_video_id
from app.services.transcripts import process_video, TranscriptError
from app.api.deps import qa_chain

router = APIRouter()

# ============ HEALTH CHECK ============
@router.get('/health')
def get_health():
    """Simple health check to ensure API is running"""
    return {"status": "ok", "message": "VidIQAI is running"}

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
        
        if not video_id:
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
    Generate a summary of a processed video.
    
    NOTE: You must call /process first with the video URL!
    """
    try:
        # Validate video ID
        if not is_valid_video_id(request.video_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video ID format"
            )
        
        # Create summary prompt
        prompt = f"Please provide a comprehensive summary of the video with ID: {request.video_id}. Include main topics, key points, and conclusions."
        
        # Get summary from QA chain
        result = qa_chain({"query": prompt})
        summary = result.get("result", "Could not generate summary")
        
        return SummaryResponse(
            summary=summary,
            video_id=request.video_id,
            transcript_length=len(summary)  # Approximate
        )
        
    except Exception as e:
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
