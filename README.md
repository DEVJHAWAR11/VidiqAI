# 🚀 Klypse: YouTube AI Chat Assistant

**Klypse** is a Chrome extension and backend system that enables users to chat with YouTube videos in real time — getting **AI-powered answers, summaries, and insights** directly on YouTube.

It combines **FastAPI**, **LangChain**, **Groq LLM**, and **Whisper** to process video transcripts and answer user queries seamlessly.

---

## 🌟 Features

- 🧠 **AI Chat with YouTube Videos** — Ask questions and get instant responses within YouTube.
- ⚡ **FastAPI Backend** — Handles transcript fetching and LLM-powered responses.
- 🌍 **Language-Aware Transcript Retrieval** — Uses Groq/Whisper fallback for videos without English subtitles.
- 🐳 **Dockerized Architecture** — Fully containerized for easy deployment.
- ☁️ **Cloud & Local Ready** — Works locally and on cloud environments like AWS EC2.

---

## 🧩 Tech Stack

**Backend:**  
- FastAPI  
- LangChain  
- Groq API  
- Whisper  
- Python  
- Docker  

**Frontend:**  
- Chrome Extension (JavaScript)

**DevOps:**  
- Docker  
- AWS EC2  
- ffmpeg  

**Other Tools:**  
- youtube-transcript-api  
- yt-dlp  

git clone https://github.com/your-username/klypse.git
cd klypse
