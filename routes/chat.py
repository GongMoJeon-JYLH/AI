from fastapi import APIRouter
from pydantic import BaseModel
from lightrag import QueryParam
from models.deepseek_lightrag import get_rag_instance
from services.session_store import user_sessions, save_user_recommendations
from services.keyword_extractor import extract_keywords
import json

router = APIRouter()

class ChatRequest(BaseModel):
    userMessage: str
    userId: str

class ChatResponse(BaseModel):
    responseText: str
    canRecommend: bool

@router.post("/chat", response_model=ChatResponse)
async def chat_handler(req: ChatRequest):
    rag = await get_rag_instance()
    user_id = req.userId
    user_message = req.userMessage

    # 책 관련 질문인지 필터
    if not any(keyword in user_message for keyword in ["책", "도서", "작가", "추천", "소설", "문학", "만화", "읽을거리"]):
        return {
            "responseText": "죄송해요. 저는 책과 관련된 질문만 도와드릴 수 있어요. 📚",
            "canRecommend": False
        }

    # 세션 초기화
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "messages": [],
            "keywords": [],
            "can_recommend": False,
            "recommended_titles": []
        }

    session = user_sessions[user_id]
    session["messages"].append(user_message)

    # 키워드 추출
    keywords = extract_keywords(user_message)
    session["keywords"].extend(kw for kw in keywords if kw not in session["keywords"])

    # 키워드가 충분하면 추천 가능 상태 전환
    if len(session["keywords"]) >= 2:
        session["can_recommend"] = True

        # RAG로 추천 책 제목 여러 개 추출
        system_prompt = (
            "너는 책 추천 시스템이야. 사용자와의 대화에서 추천할 수 있는 책 제목을 최대 3개까지 JSON으로 반환해.\n"
            "형식: {\"titles\": [\"추천 책 제목1\", \"추천 책 제목2\", \"추천 책 제목3\"]} 외 텍스트 금지"
        )
        query = "사용자와의 대화: " + " ".join(session["messages"])
        response = rag.query(query, param=QueryParam(system_prompt=system_prompt))

        try:
            book_titles = json.loads(response).get("titles", [])
            session["recommended_titles"] = book_titles[:3]
            title_preview = "', '".join(session["recommended_titles"])
        except:
            session["recommended_titles"] = []
            title_preview = ""

        return {
            "responseText": f"추천드릴 책이 있어요! 📚 '{title_preview}' 을(를) 곧 알려드릴게요.",
            "canRecommend": True
        }

    # 아직 추천 불가 - 사용자 맞춤 질문 유도
    system_prompt = (
        "너는 책 추천을 위한 인터뷰어야. 사용자의 발화를 바탕으로, 관심사나 감정을 더 잘 파악할 수 있는 후속 질문 하나만 자연스럽게 생성해.\n"
        "형식: 사용자에게 자연스럽게 이어지는 한 문장의 질문만 출력. 예: '최근 읽은 책 중 가장 인상 깊었던 건 무엇이었나요?'"
    )
    context = "지금까지 사용자 대화: " + " ".join(session["messages"])
    followup = rag.query(context, param=QueryParam(system_prompt=system_prompt))

    return {
        "responseText": followup,
        "canRecommend": False
    }
