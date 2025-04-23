from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from lightrag import QueryParam
from models.deepseek_lightrag import get_rag_instance
from services.session_store import user_sessions, user_exists, get_user_name
from services.keyword_extractor import extract_keywords_from_gpt
from services.utils import parse_json_from_response
import asyncio
from services.user_type_extractor import save_user_type_async
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

    if not user_exists(user_id):
        raise HTTPException(status_code=401, detail="존재하지 않는 사용자입니다. 먼저 /users에서 등록해 주세요.")

    session = user_sessions[user_id]
    session["messages"].append({"role": "user", "content": user_message})
    user_name = get_user_name(user_id)

    keywords = await extract_keywords_from_gpt(user_message)
    session["keywords"].extend(kw for kw in keywords if kw not in session["keywords"])

    if len(session["keywords"]) >= 3:
        session["can_recommend"] = True

        recommend_system_prompt = """
        너는 책 추천 시스템이야. 사용자와의 대화에서 추천할 수 있는 책 제목을 무조건 3개 JSON으로 반환해.
        title에 해당하는 제목만 말해줘.
        형식: {{ "titles": ["추천 책 제목1", "추천 책 제목2", "추천 책 제목3"] }} 외 텍스트 금지
        """
        query = "사용자와의 대화:\n" + "\n".join(f"{m['role']}: {m['content']}" for m in session["messages"])
        response = await rag.aquery(
            query,
            param=QueryParam(mode="local", conversation_history=session["messages"], history_turns=5),
            system_prompt=recommend_system_prompt
        )

        with open("books_with_age.json", "r", encoding="utf-8") as f:
            book_data = json.load(f)
        db_titles = set(book["title"] for book in book_data)

        book_titles = parse_json_from_response(response, key="titles") or []
        # ✅ 부분 일치로 필터링
        filtered_titles = [
            candidate for candidate in book_titles
            if any(candidate in db_title for db_title in db_titles)
        ]

        if filtered_titles:
            session["recommended_titles"] = filtered_titles[:3]
            asyncio.create_task(save_user_type_async(user_id, session["messages"]))
            title_preview = "', '".join(session["recommended_titles"])
            responseText = f"{user_name}님께 추천드릴 책이 있어요! 📚 '{title_preview}' 을(를) 곧 알려드릴게요."
            session["messages"].append({"role": "assistant", "content": responseText})
            return {"responseText": responseText, "canRecommend": True}
        else:
            session["can_recommend"] = False
            session["recommended_titles"] = []

    # 추가 정보 유도 질문
    interview_prompt = f"""
    너는 책 MBTI 테스트의 인터뷰어야. 사용자({user_name}님)의 성격과 라이프스타일을 파악해서 책을 추천하기 위한 자연스러운 질문을 하나 생성해.
    질문은 대화체로 짧게 말해줘. 예: '주말엔 혼자 쉬는 걸 좋아하세요, 친구들과 어울리는 걸 좋아하세요?', '학교에 다니시나요?'
    """
    context = "지금까지 사용자 대화: " + " ".join(m["content"] for m in session["messages"])
    followup = await rag.aquery(
        context,
        param=QueryParam(mode="global", conversation_history=session["messages"], history_turns=5),
        system_prompt=interview_prompt
    )

    session["messages"].append({"role": "assistant", "content": followup})
    return {"responseText": followup, "canRecommend": False}
