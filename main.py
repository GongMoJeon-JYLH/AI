from fastapi import FastAPI
from routes.recommendation import router as recommendation_router
from routes.chat import router as chat_router
from routes.users import router as user_router
from fastapi.middleware.cors import CORSMiddleware
from services.logger_middleware import LoggingMiddleware

app = FastAPI(
    title="도서 추천 챗봇 API",
    description="채팅을 통한 사용자의 입력에서 관심 키워드를 추출하고, 도서 데이터 중 유사한 책을 추천합니다.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(user_router, tags=["유저 ID 생성"])
app.include_router(chat_router, tags=["채팅"])
app.include_router(recommendation_router, tags=["도서 추천"])