from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM Configuration
    LLM_PROVIDER: str = "groq"  # Default to Groq
    
    # Groq Settings (Best free option)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # GPT-4 level quality
    
    # OpenAI (Backup - if you add credits later)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Storage Paths
    CHROMA_DB_PATH: str
    CACHE_PATH: str
    
    # Server Configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = '.env'

config = Settings()

# Validation
if config.LLM_PROVIDER == 'groq' and not config.GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is required when using Groq")
