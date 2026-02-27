# app/api/endpoints.py

import asyncio
import os
import re
import uuid
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import AskRequest
from app.storage.vector_store import load_vectorstore_for_video, create_vectorstore_for_video
from app.services.qa_chain import create_qa_chain
from app.api.deps import llm
from app.storage.cache import load_transcript
from app.services.transcripts import get_transcript

router = APIRouter()
logger = logging.getLogger(__name__)


def remove_consecutive_duplicates(text: str) -> str:
    """
    Remove consecutive duplicate words from LLM output before streaming.

    Handles three patterns:
      1. Plain word duplicates:      'AWS AWS caused'   -> 'AWS caused'
      2. Punctuated duplicates:      'economy, economy,' -> 'economy,'
      3. Multi-occurrence cleanup:   iterates word-by-word with normalization

    This is a post-processing step to handle LLM repetition artifacts
    that occasionally appear in streamed outputs from quantized models.
    """
    # Pattern 1: word-level duplicates
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
    # Pattern 2: punctuated duplicates
    text = re.sub(r'\b(\w+)([.,;:!?]?)\s+\1\2\b', r'\1\2', text, flags=re.IGNORECASE)
    # Pattern 3: word-by-word pass
    words = text.split()
    cleaned = []
    prev_word = None
    for word in words:
        word_normalized = re.sub(r'[^\w]', '', word).lower()
        if word_normalized != prev_word or word_normalized == '':
            cleaned.append(word)
            prev_word = word_normalized
    return ' '.join(cleaned)


@router.get(
    '/check/{video_id}',
    summary="Check transcript availability",
    description="""
    Checks whether a transcript or FAISS vectorstore already exists for the given video_id.
    Falls back to a live transcript fetch if neither cache nor vectorstore is found.
    Returns `{"status": "available"}` or `{"status": "unavailable"}`.
    """
)
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
    except Exception:
        pass

    return {"status": "unavailable"}


@router.post(
    '/ask/stream',
    summary="Stream AI answer via SSE",
    description="""
    Core Q&A endpoint. Accepts a `video_id` and `question`, returns a
    **Server-Sent Events (SSE)** stream of the AI answer word-by-word.

    **Flow:**
    1. If FAISS vectorstore exists for `video_id` → load and query immediately.
    2. If not → trigger the 4-tier transcript pipeline:
       - Tier 1: YouTubeTranscriptApi (10 languages)
       - Tier 2: Groq Whisper API (audio < 24MB)
       - Tier 3: Local Whisper model (any size)
    3. Chunk transcript → embed → store in per-video FAISS index.
    4. Run LangChain RetrievalQA (MMR, k=3) → stream answer.

    **Streaming format:** `data: <word>\\n\\n` ... `data: [END]\\n\\n`
    """
)
async def ask_question_stream(body: AskRequest):
    video_id = body.video_id
    question = body.question

    logger.info(f"REQ {uuid.uuid4()}: video_id={video_id}, question_len={len(question)}")

    if not video_id or not question:
        async def error_stream():
            yield "data: ❌ Missing video ID or question\n\n"
            yield "data: [END]\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

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
                answer = str(result.get('result', result.get('answer', str(result)))).strip()
                answer = remove_consecutive_duplicates(answer)
                logger.info(f"Answer preview: {answer[:200]}")

                words = answer.split()
                prev_word = None
                for word in words:
                    word_clean = word.strip()
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

    # Vectorstore already exists — query directly
    qa_chain = create_qa_chain(llm, vectorstore)

    async def event_stream():
        try:
            result = qa_chain.invoke({"query": question})
            answer = str(result.get('result', result.get('answer', str(result)))).strip()
            answer = remove_consecutive_duplicates(answer)
            logger.info(f"Answer preview: {answer[:200]}")

            words = answer.split()
            prev_word = None
            for word in words:
                word_clean = word.strip()
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
