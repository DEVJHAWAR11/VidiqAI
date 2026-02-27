# Klypse — YouTube Video Intelligence Engine

> Ask any question about any YouTube video. Get AI-powered answers streamed in real time.

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-orange)](https://langchain.com)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](../LICENSE)

---

## 📺 Demo

> **[Watch Full Workflow Demo ▶](https://youtu.be/XX2n9f3PlNs)** — includes AWS EC2 deployment, live Q&A, YouTube IP restriction diagnosis, and local fallback validation.

---

## Architecture

```
Chrome Extension (JavaScript)
        │  POST { video_id, question }
        ▼
FastAPI Backend  /ask/stream
        │
        ├── FAISS store exists? ──YES──► RetrievalQA Chain ─► SSE Word Stream
        │
       NO
        │
        ▼
Transcript Pipeline (4-tier fallback)
  ① YouTubeTranscriptApi  — tries 10 languages (en, hi, es, fr, de, ru, ar, bn, id)
  ② Groq Whisper API      — downloads audio via yt-dlp, transcribes (files < 24MB)
  ③ Local Whisper Model   — fully offline fallback for any file size
        │
        ▼
  clean_text() → chunk_text(size=500, overlap=50)
        │
        ▼
  FAISS Vector Store (per-video index, persisted to ./data/faiss/{video_id}/)
        │
        ▼
  LangChain RetrievalQA
    └─ search_type: MMR (Maximum Marginal Relevance)
    └─ k=3 chunks, fetch_k=10 candidates
    └─ LLM: Groq LLaMA-3.3-70b-versatile
        │
        ▼
  Word-by-word SSE stream with deduplication post-processing
        │
        ▼
Chrome Extension renders streamed response in real time
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
| Frontend | Chrome Extension (JavaScript) |
| Containerization | Docker + docker-compose |
| Cloud | AWS EC2 (with documented IP restriction workaround) |

---

## Key Engineering Decisions

### 1. Per-video FAISS Index (not a shared index)
Each video gets its own FAISS index at `./data/faiss/{video_id}/`. This means:
- **Zero cross-video context contamination** — answers are always grounded in the correct video
- **Instant load on repeated queries** — no re-embedding on subsequent questions
- **Disk-persisted** — survives server restarts

### 2. 4-Tier Transcript Fallback
YouTube’s API does not guarantee transcript availability. The pipeline tries every method before failing:
- **Tier 1:** Official subtitles via `YouTubeTranscriptApi` (10 languages in priority order)
- **Tier 2:** Groq Whisper API — downloads audio via `yt-dlp`, transcribes via cloud (fast, limited to 24MB)
- **Tier 3:** Local Whisper model — fully offline, handles any file size (slower)
- **Result:** Works on virtually any video that has audio

### 3. MMR Retrieval (Maximum Marginal Relevance)
Switched from standard similarity search to MMR retrieval in `qa_chain.py`. MMR selects chunks that are both **relevant** to the query and **diverse** from each other, preventing the LLM from receiving redundant context when multiple similar transcript segments exist.

### 4. AWS IP Restriction — Diagnosed & Documented
During AWS EC2 deployment, YouTube began blocking requests originating from cloud IPs (standard anti-scraping policy). The issue was:
- **Diagnosed** via `yt-dlp` verbose logs showing HTTP 403 from AWS-origin requests
- **Confirmed** by comparing direct EC2 curl vs. local curl responses
- **Resolved** via a local-fallback strategy ensuring service reliability
- **Proven** via a [recorded demo video](https://youtu.be/XX2n9f3PlNs) showing full functionality

### 5. SSE Streaming with Deduplication
Answers stream word-by-word using FastAPI’s `StreamingResponse` with `text/event-stream` MIME type. A post-processing deduplication step (`remove_consecutive_duplicates`) handles repetition artifacts that occasionally appear in streamed outputs from quantized LLMs.

---

## Project Structure

```
VidiqAI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints.py     # /check and /ask/stream routes (SSE)
│   │   │   ├── auth.py          # API key dependency
│   │   │   └── deps.py          # LLM initialization (Groq)
│   │   ├── services/
│   │   │   ├── transcripts.py   # 4-tier transcript pipeline
│   │   │   ├── qa_chain.py      # LangChain RetrievalQA + custom prompt
│   │   │   ├── embeddings.py    # Embedding model config
│   │   │   └── processing.py    # Text cleaning + chunking
│   │   ├── storage/
│   │   │   ├── vector_store.py  # FAISS create/load operations
│   │   │   └── cache.py         # Transcript disk cache
│   │   ├── config.py        # Pydantic settings (env-based)
│   │   └── main.py          # FastAPI app entrypoint + CORS
│   ├── docker/
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── .env.example         # Copy to .env and fill in your keys
└── chrome-extension/        # JS frontend (loads on YouTube pages)
```

---

## Setup & Run

### Prerequisites
- Docker + docker-compose
- A free [Groq API key](https://console.groq.com)
- ffmpeg (for audio fallback; installed inside Docker automatically)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/DEVJHAWAR11/VidiqAI.git
cd VidiqAI/backend

# 2. Configure environment
cp .env.example .env
# Open .env and add your GROQ_API_KEY

# 3. Build and run with Docker
docker-compose up --build

# 4. Backend is live at http://localhost:8000
# 5. Interactive API docs at http://localhost:8000/docs
```

### Chrome Extension
1. Open Chrome → `chrome://extensions/`
2. Enable **Developer Mode**
3. Click **Load unpacked** → select the `chrome-extension/` folder
4. Navigate to any YouTube video and open the extension

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API info + version |
| `GET` | `/health` | Service health check |
| `GET` | `/check/{video_id}` | Check transcript/vectorstore availability |
| `POST` | `/ask/stream` | Stream AI answer via SSE |

**POST `/ask/stream` request body:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "question": "What is the main topic of this video?"
}
```

**SSE Stream format:**
```
data: The

data: main

data: topic

data: [END]
```

---

## Known Constraints

| Constraint | Details |
|---|---|
| AWS IP blocking | YouTube blocks transcript/audio requests from AWS-hosted servers. Workaround: run locally or use a residential proxy. Full diagnosis and demo in [video](https://youtu.be/XX2n9f3PlNs). |
| Groq Whisper file limit | Groq’s Whisper API accepts audio files up to 24MB. Larger files fall back to local Whisper automatically. |
| Local Whisper speed | Local Whisper (base model) is slower than the cloud API — expect 30–60s for long videos on CPU. |

---

## Author

**Dev Jhawar** — [GitHub](https://github.com/DEVJHAWAR11) | KIIT University, CSE (CGPA: 9.66)
