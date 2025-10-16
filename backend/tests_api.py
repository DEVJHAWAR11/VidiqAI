# Create test_api.py in your project root
from app.config import config

print(f"Provider: {config.LLM_PROVIDER}")
print(f"Model: {config.OPENAI_MODEL}")
print(f"API Key (first 10 chars): {config.OPENAI_API_KEY[:10]}...")
print("✓ Configuration loaded successfully!")
