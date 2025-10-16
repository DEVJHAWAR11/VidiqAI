from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM Configuration
    LLM_PROVIDER: str
    OPENAI_API_KEY: str
    
    # Model Selection - NEW!
    OPENAI_MODEL: str = "gpt-4o-mini"  # Default model
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"  # Default embeddings
    
    # Storage
    CHROMA_DB_PATH: str
    CACHE_PATH: str
    
    # Server
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = '.env'

config = Settings()

# Validation
if config.LLM_PROVIDER == 'openai' and not config.OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is required when using OpenAI")
