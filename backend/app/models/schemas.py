from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class ProcessVideoRequest(BaseModel):
    """Request model for processing a video"""
    video_url: str = Field(..., description="YouTube video URL or video ID")
    
    @field_validator('video_url')
    def validate_video_url(cls, v):
        """Ensure it's a valid YouTube URL or video ID"""
        if not v:
            raise ValueError("video_url cannot be empty")
        return v

class ProcessVideoResponse(BaseModel):
    """Response after processing a video"""
    status: str
    video_id: str
    video_url: str
    message: str
    chunks_created: int
    transcript_length: int

class AskQuestionRequest(BaseModel):
    """Request model for asking a question"""
    video_id: str = Field(..., description="YouTube video ID")
    question: str = Field(..., min_length=3, description="User's question")

class AskQuestionResponse(BaseModel):
    """Response with answer to user's question"""
    answer: str
    video_id: str
    question: str
    sources_used: int

class SummaryRequest(BaseModel):
    """Request model for video summary"""
    video_id: str = Field(..., description="YouTube video ID")

class SummaryResponse(BaseModel):
    """Response with video summary"""
    summary: str
    video_id: str
    transcript_length: int

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
