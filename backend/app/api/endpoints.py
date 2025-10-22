# app/api/endpoints.py

import asyncio
import os
import re
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import AskRequest
from app.storage.vector_store import load_vectorstore_for_video, create_vectorstore_for_video
from app.services.qa_chain import create_qa_chain
from app.api.deps import llm
from app.storage.cache import load_transcript
from app.services.transcripts import get_transcript

router = APIRouter()

@router.get('/check/{video_id}')
def check_transcript_status(video_id: str):
    transcript = load_transcript(video_id)
    if transcript:
        return {"status": "available"}
    
    vectorstore_path = f"./data/faiss/{video_id}/"
    if os.path.exists(vectorstore_path):
        return {"status": "available"}
    
    try:
        transcript = get_transcript(video_id)
        if transcript:
            return {"status": "available"}
    except:
        pass
    
    return {"status": "unavailable"}

import uuid
import logging

logger = logging.getLogger(__name__)

def remove_consecutive_duplicates(text: str) -> str:
    """
    Remove consecutive duplicate words from text.
    Example: "AWS AWS caused" -> "AWS caused"
    Example: "economy, economy," -> "economy,"
    """
    # Pattern 1: Remove word-level duplicates (with punctuation handling)
    # Matches: word followed by space(s) and the same word
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
    
    # Pattern 2: Remove duplicates with punctuation
    # Matches: word with punctuation followed by space and same word with punctuation
    text = re.sub(r'\b(\w+)([.,;:!?]?)\s+\1\2\b', r'\1\2', text, flags=re.IGNORECASE)
    
    # Pattern 3: Clean up any remaining multiple consecutive duplicates
    words = text.split()
    cleaned = []
    prev_word = None
    
    for word in words:
        # Normalize for comparison (remove punctuation)
        word_normalized = re.sub(r'[^\w]', '', word).lower()
        if word_normalized != prev_word or word_normalized == '':
            cleaned.append(word)
            prev_word = word_normalized
    
    return ' '.join(cleaned)

@router.post('/ask/stream')
async def ask_question_stream(body: AskRequest):
    video_id = body.video_id
    question = body.question
    
    logger.info(f"REQ {uuid.uuid4()}: incoming QA request: video_id={video_id}, question_len={len(question)}")
    
    # CRITICAL: Validate inputs
    if not video_id or not question:
        async def error_stream():
            yield "data: ❌ Missing video ID or question\n\n"
            yield "data: [END]\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    # CRITICAL: Ensure question is a clean string
    question = str(question).strip()
    if not question:
        async def error_stream():
            yield "data: ❌ Question cannot be empty\n\n"
            yield "data: [END]\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    try:
        vectorstore = load_vectorstore_for_video(video_id)
    except FileNotFoundError:
        async def processing_stream():
            yield "data: 🔄 Processing video...\n\n"
            await asyncio.sleep(0.2)
            
            transcript = load_transcript(video_id)
            if not transcript:
                try:
                    transcript = get_transcript(video_id)
                except Exception as e:
                    yield f"data: ❌ Could not fetch transcript: {str(e)}\n\n"
                    yield "data: [END]\n\n"
                    return
            
            yield "data: 🧠 Creating embeddings...\n\n"
            await asyncio.sleep(0.2)
            
            try:
                create_vectorstore_for_video(video_id, transcript)
                vectorstore = load_vectorstore_for_video(video_id)
            except Exception as e:
                yield f"data: ❌ Error creating embeddings: {str(e)}\n\n"
                yield "data: [END]\n\n"
                return
            
            yield "data: ✅ Ready!\n\n\n"
            await asyncio.sleep(0.2)
            
            try:
                qa_chain = create_qa_chain(llm, vectorstore)
                result = qa_chain.invoke({"query": question})
                answer = result.get('result', result.get('answer', str(result)))
                
                # Ensure answer is string and clean
                answer = str(answer).strip()
                
                # CRITICAL: Apply aggressive deduplication before streaming
                answer = remove_consecutive_duplicates(answer)
                
                # Log cleaned answer
                logger.info(f"Cleaned answer (first 200 chars): {answer[:200]}")
                
                # Stream word by word with deduplication check
                words = answer.split()
                prev_word = None
                for word in words:
                    word_clean = word.strip()
                    # Additional check: don't send if same as previous
                    word_normalized = re.sub(r'[^\w]', '', word_clean).lower()
                    if word_normalized != prev_word or word_normalized == '':
                        yield f"data: {word_clean}\n\n"
                        await asyncio.sleep(0.04)
                        prev_word = word_normalized
                    
            except Exception as e:
                logger.error(f"Error generating answer: {str(e)}")
                yield f"data: ❌ Error generating answer: {str(e)}\n\n"
            
            yield "data: [END]\n\n"
        
        return StreamingResponse(processing_stream(), media_type="text/event-stream")
    
    # Vectorstore exists
    qa_chain = create_qa_chain(llm, vectorstore)
    
    async def event_stream():
        try:
            result = qa_chain.invoke({"query": question})
            answer = result.get('result', result.get('answer', str(result)))
            
            # Ensure answer is string and clean
            answer = str(answer).strip()
            
            # CRITICAL: Apply aggressive deduplication before streaming
            answer = remove_consecutive_duplicates(answer)
            
            # Log cleaned answer
            logger.info(f"Cleaned answer (first 200 chars): {answer[:200]}")
            
            # Stream word by word with deduplication check
            words = answer.split()
            prev_word = None
            for word in words:
                word_clean = word.strip()
                # Additional check: don't send if same as previous
                word_normalized = re.sub(r'[^\w]', '', word_clean).lower()
                if word_normalized != prev_word or word_normalized == '':
                    yield f"data: {word_clean}\n\n"
                    await asyncio.sleep(0.04)
                    prev_word = word_normalized
                
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            yield f"data: ❌ Error: {str(e)}\n\n"
        
        yield "data: [END]\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
