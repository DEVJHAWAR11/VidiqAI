# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.config import config

app = FastAPI(
    title="Klypse API",
    description="""
## Klypse — YouTube Video Intelligence Engine

A production-grade AI backend that enables real-time Q&A on any YouTube video.

### Architecture
- **Transcript Pipeline**: 4-tier fallback (YT API → multi-language → Groq Whisper → Local Whisper)
- **Vector Store**: Per-video FAISS index with LangChain RetrievalQA (MMR retrieval)
- **LLM**: Groq LLaMA-3.3-70b with word-by-word SSE streaming
- **Deployment**: Dockerized, AWS EC2 compatible with documented local fallback strategy

### Endpoints
- `GET /check/{video_id}` — Check transcript/vectorstore availability
- `POST /ask/stream` — Stream AI answer via Server-Sent Events
    """,
    version="1.0.0",
    contact={"name": "Dev Jhawar", "url": "https://github.com/DEVJHAWAR11/VidiqAI"},
    license_info={"name": "MIT"}
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(endpoints.router)

@app.get("/", summary="Root", description="Returns API name and version.")
def root():
    return {"message": "Klypse API", "version": "1.0.0", "docs": "/docs"}

@app.get("/health", summary="Health Check", description="Returns service health status.")
def health():
    return {"status": "healthy"}
