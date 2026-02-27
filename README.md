# Klypse — YouTube Video Intelligence Engine

> Ask any question about any YouTube video. Get AI-powered answers streamed in real time.

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-orange)](https://langchain.com)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> 🌐 **Live Demo:** [klypse-ai-youtube-extension-bot.netlify.app](https://klypse-ai-youtube-extension-bot.netlify.app/)

---

## What is Klypse?

Klypse is a **Chrome extension + FastAPI backend** that lets you ask questions about any YouTube video and get AI-powered answers in real time. It handles videos with no subtitles, non-English content, and works offline via a local Whisper fallback.

---

## Architecture

```
Chrome Extension (JavaScript)
        │  POST { video_id, question }
        ▼
FastAPI Backend  /ask/stream
        │
        ├─ FAISS store exists? ─YES─► RetrievalQA (MMR, k=3) ─► SSE Word Stream
        │
       NO
        ▼
Transcript Pipeline (4-tier fallback)
  ① YouTubeTranscriptApi  — tries 10 languages (en, hi, es, fr, de, ru, ar, bn, id)
  ② Groq Whisper API      — downloads audio via yt-dlp, transcribes (files < 24MB)
  ③ Local Whisper Model   — fully offline, any file size
        ▼
  clean_text() → chunk_text(size=500) → FAISS Vector Store (per-video, disk-persisted)
        ▼
  LangChain RetrievalQA → Groq LLaMA-3.3-70b → SSE Stream → Chrome Extension
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Python 3.10 |
| LLM | Groq API (LLaMA-3.3-70b-versatile) |
| Orchestration | LangChain RetrievalQA |
| Retrieval | FAISS + MMR (per-video, disk-persisted) |
| Transcription | YouTubeTranscriptApi + Groq Whisper + Local Whisper |
| Audio Download | yt-dlp + ffmpeg |
| Frontend | Chrome Extension (JavaScript) + Netlify Landing Page |
| Containerization | Docker + docker-compose |
| Cloud | AWS EC2 (with documented IP restriction workaround) |

---

## Key Engineering Decisions

### 1. Per-video FAISS Index
Each video gets its own FAISS index at `./data/faiss/{video_id}/` — zero cross-video context contamination, instant load on repeated queries, survives server restarts.

### 2. 4-Tier Transcript Fallback
- **Tier 1:** Official subtitles via YouTubeTranscriptApi (10 languages)
- **Tier 2:** Groq Whisper API — cloud transcription for audio < 24MB
- **Tier 3:** Local Whisper model — fully offline, any file size
- Works on virtually any video that has audio

### 3. MMR Retrieval
Uses Maximum Marginal Relevance instead of plain similarity search — retrieves chunks that are both **relevant** and **diverse**, preventing redundant context from similar transcript segments.

### 4. AWS IP Restriction — Diagnosed & Documented
YouTube blocks requests from AWS cloud IPs. Issue was diagnosed via yt-dlp verbose logs (HTTP 403 from AWS-origin), confirmed by comparing EC2 vs local curl responses, resolved via local-fallback strategy, and proven via live demo on the landing page.

### 5. SSE Streaming with Deduplication
Answers stream word-by-word via `StreamingResponse` with `text/event-stream`. Post-processing deduplication handles repetition artifacts from streamed LLM outputs.

---

## Project Structure

```
VidiqAI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints.py     # /check and /ask/stream (SSE streaming)
│   │   │   ├── auth.py          # API key dependency
│   │   │   └── deps.py          # LLM initialization
│   │   ├── services/
│   │   │   ├── transcripts.py   # 4-tier transcript pipeline
│   │   │   ├── qa_chain.py      # LangChain RetrievalQA + MMR + custom prompt
│   │   │   ├── embeddings.py    # Embedding model config
│   │   │   └── processing.py    # Text cleaning + chunking
│   │   ├── storage/
│   │   │   ├── vector_store.py  # FAISS create/load
│   │   │   └── cache.py         # Transcript disk cache
│   │   ├── config.py        # Pydantic settings (env-based)
│   │   └── main.py          # FastAPI app + CORS
│   ├── docker/
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── .env.example
└── chrome-extension/        # JS frontend (injects into YouTube pages)
```

---

## Setup & Run

```bash
# 1. Clone
git clone https://github.com/DEVJHAWAR11/VidiqAI.git
cd VidiqAI/backend

# 2. Configure environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 3. Run with Docker
docker-compose up --build

# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Chrome Extension:**
1. Chrome → `chrome://extensions/` → Enable Developer Mode
2. Load unpacked → select `chrome-extension/` folder
3. Open any YouTube video and use the extension

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API info + version |
| `GET` | `/health` | Service health check |
| `GET` | `/check/{video_id}` | Check transcript/vectorstore availability |
| `POST` | `/ask/stream` | Stream AI answer via SSE |

**Request body for `/ask/stream`:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "question": "What is the main topic of this video?"
}
```

---

## Known Constraints

| Constraint | Details |
|---|---|
| AWS IP blocking | YouTube blocks requests from AWS-hosted servers. Full diagnosis documented; working demo on [landing page](https://klypse-ai-youtube-extension-bot.netlify.app/). |
| Groq Whisper limit | Audio files > 24MB fall back to local Whisper automatically. |
| Local Whisper speed | Base model ~30–60s for long videos on CPU. |

---

## Author

**Dev Jhawar** — [GitHub](https://github.com/DEVJHAWAR11) | KIIT University, CSE (CGPA: 9.66)
