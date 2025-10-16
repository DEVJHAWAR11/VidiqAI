from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints

app = FastAPI(
    title='VidIQAI',
    description='YouTube Video Chatbot API with RAG',
    version='1.0.0'
)

# CORS - This is BACKEND code, not UI!
# It tells FastAPI to accept requests from browsers (future Chrome extension)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register your API routes
app.include_router(endpoints.router, prefix="/api/v1", tags=["VidIQAI"])

@app.get("/")
def read_root():
    return {
        "message": "VidIQAI API is running",
        "docs": "/docs",
        "version": "1.0.0"
    }


