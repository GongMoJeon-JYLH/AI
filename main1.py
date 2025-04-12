from fastapi import FastAPI
from routes.recommendation import router as recommendation_router
from routes.chat import router as chat_router

app = FastAPI()
app.include_router(recommendation_router)
app.include_router(chat_router)