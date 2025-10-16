from fastapi import FastAPI
from app.api import endpoints
app=FastAPI(title='vidiqAI')

app.include_router(endpoints.router)

