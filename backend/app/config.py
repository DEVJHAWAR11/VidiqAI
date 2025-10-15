from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_PROVIDER:str
    OPENAI_API_KEY:str
    CHROMA_DB_PATH:str
    CACHE_PATH:str
    APP_HOST:str
    APP_PORT:int
    LOG_LEVEL:str
    
    class Config:
        env_file='.env'
        

config=Settings()

if config.LLM_PROVIDER =='openai' and not config.OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is required for OpenAI LLM_PROVIDER")



