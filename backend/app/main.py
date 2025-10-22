# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.config import config

app = FastAPI(
    title="KLYPSE API",
    description="YouTube Video Q&A with AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",
        "http://localhost:*",
        "https://www.youtube.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(endpoints.router, prefix="/api/v1", tags=["videos"])

@app.get("/")
def root():
    return {"message": "VidIQAI API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
