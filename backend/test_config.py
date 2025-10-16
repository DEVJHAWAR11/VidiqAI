# test_config.py - Place this in backend/ folder

from app.config import config

print("=" * 50)
print("Configuration Test")
print("=" * 50)
print(f"Provider: {config.LLM_PROVIDER}")
print(f"Model: {config.OPENAI_MODEL}")
print(f"Embedding Model: {config.OPENAI_EMBEDDING_MODEL}")
print(f"API Key (first 10 chars): {config.OPENAI_API_KEY[:10]}...")
print(f"Chroma DB Path: {config.CHROMA_DB_PATH}")
print(f"Cache Path: {config.CACHE_PATH}")
print("=" * 50)
print("✓ Configuration loaded successfully!")
print("=" * 50)
