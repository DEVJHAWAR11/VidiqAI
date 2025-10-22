# Python base image
FROM python:3.10-slim

# Set a working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install system dependencies (ffmpeg for audio, etc)
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy rest of your app
COPY . .

# Environment variables (set these securely in production)
ENV PYTHONUNBUFFERED 1

# Expose FastAPI default port
EXPOSE 8000

# Command to run your backend (edit as needed)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
