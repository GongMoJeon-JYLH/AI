from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from models.deepseek_model import handle_conversation

router = APIRouter()

# 요청 형식
class ChatRequest(BaseModel):
    userId: int
    messages: List[str]

# 응답 형식
class ChatResponse(BaseModel):
    responseText: str
    canRecommend: bool

@router.post("/chat", response_model=ChatResponse)
def chat_handler(req: ChatRequest):
    response, canRecommend = handle_conversation(user_id=req.userId, messages=req.messages)
    return {"responseText": response, "canRecommend": canRecommend}
