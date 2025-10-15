from fastapi import FastAPI

from app.config import config

print(config.APP_HOST)
print(config.CHROMA_DB_PATH)
