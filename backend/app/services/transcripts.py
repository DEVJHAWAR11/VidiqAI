import os
from youtube_transcript_api import YouTubeTranscriptApi, _errors
from app.storage.cache import save_transcript, load_transcript
from app.storage.vector_store import add_to_vectorstore
from app.services.processing import chunk_text, clean_text
from app.utils.logger import get_logger
import yt_dlp
from groq import Groq
from app.config import config
import whisper

logger = get_logger(__name__)

class TranscriptError(Exception):
    """Custom exception for transcript errors"""
    pass

def download_audio(video_url: str, output_dir: str = "./data/audio") -> str:
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        audio_path = os.path.join(output_dir, f"{info['id']}.mp3")
        logger.info(f"✓ Downloaded audio: {audio_path}")
        return audio_path

def transcribe_with_groq(audio_path: str) -> str:
    client = Groq(api_key=config.GROQ_API_KEY)
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), file.read()),
            model="whisper-large-v3",
            response_format="text",
            temperature=0.0,
        )
    logger.info("✓ Groq transcription complete")
    return transcription

def transcribe_with_local_whisper(audio_path: str, model_size="base") -> str:
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    logger.info("✓ Local Whisper transcription complete")
    return result["text"]

def get_transcript(video_id: str, video_url: str = None):
    # Step 1: Try transcript cache
    cached = load_transcript(video_id)
    if cached:
        logger.info(f"✓ Using cached transcript for: {video_id}")
        return cached

    # Step 2: Try all likely transcript languages
    languages = [
        'en', 'hi', 'es', 'fr', 'de', 'ru', 'ar', 'bn', 'id', 'auto'
    ]
    for lang in languages:
        try:
            logger.info(f"Trying transcript for language: {lang}")
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            transcript_text = " ".join([entry['text'] for entry in transcript_data])
            save_transcript(video_id, transcript_text)
            logger.info(f"✓ Got transcript ({lang}, {len(transcript_text)} chars)")
            return transcript_text
        except _errors.NoTranscriptFound as e:
            logger.info(f"✗ No transcript in {lang}: {str(e)}")
        except Exception as e:
            logger.info(f"✗ Other error for lang {lang}: {str(e)}")
        continue

    # Step 3: Groq fallback for short videos only (<25MB audio)
    logger.info("No transcript found for any language. Trying Groq Whisper API...")
    try:
        if not video_url:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        audio_path = download_audio(video_url)
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        logger.info(f"Audio file size: {file_size_mb:.2f} MB")
        if file_size_mb <= 24:
            try:
                grq_txt = transcribe_with_groq(audio_path)
                save_transcript(video_id, grq_txt)
                os.remove(audio_path)
                return grq_txt
            except Exception as groq_error:
                logger.warning(f"Groq failed: {str(groq_error)}")
        else:
            logger.warning("Audio file too large for Groq fallback; trying local Whisper")

        # Step 4: Local Whisper fallback (any file size)
        w_txt = transcribe_with_local_whisper(audio_path)
        save_transcript(video_id, w_txt)
        os.remove(audio_path)
        return w_txt

    except Exception as whisper_error:
        logger.error(f"All approaches failed: {str(whisper_error)}")
        raise TranscriptError(
            "No transcript could be retrieved for this video (even with local Whisper fallback). "
            "This may be a platform restriction or severe audio download error. Contact admin if this is unexpected."
        )

def process_video(video_id: str, video_url: str = None) -> dict:
    logger.info(f"Starting video processing for: {video_id}")
    transcript = get_transcript(video_id, video_url)
    cleaned = clean_text(transcript)
    chunks = chunk_text(cleaned, chunk_size=500)
    add_to_vectorstore(chunks)
    logger.info(f"✓ Processed {len(chunks)} chunks into vector store")
    return {
        "video_id": video_id,
        "video_url": video_url or f"https://www.youtube.com/watch?v={video_id}",
        "transcript_length": len(transcript),
        "chunks_created": len(chunks),
        "status": "success"
    }