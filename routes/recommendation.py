from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from services.session_store import user_sessions, user_exists, get_user_type

BOOKS_JSON_PATH = "./books_with_age.json"
with open(BOOKS_JSON_PATH, "r", encoding="utf-8") as f:
    books = json.load(f)

router = APIRouter()

class Userinfo(BaseModel):
    userId: str
    name: str

class BookRecommendation(BaseModel):
    bookTitle: str
    bookReason: str
    imageUrl: str
    bookUrl: str
    bookSummary: str
    bookGenre: str

class BookRecommendationList(BaseModel):
    recommendations: list[BookRecommendation]
    keywords: list
    userType: str
    userTypeReason: str

@router.post("/book-recommend",
            response_model=BookRecommendationList,
            responses={
                401: {"description": "존재하지 않는 사용자입니다. 먼저 /users에서 등록해 주세요."},
                402: {"description": "아직 책 추천이 불가능한 상태입니다. 더 많은 대화를 나눠주세요."},
                400: {"description": "요청 형식 오류 (예: 메시지 누락)"},
                500: {"description": "서버 내부 오류"},
            }
)
def book_recommend(userinfo: Userinfo):
    user_id = userinfo.userId

    # 유저 존재 확인
    if not user_exists(user_id):
        raise HTTPException(status_code=401, detail="유저가 존재하지 않습니다. 먼저 등록해주세요.")

    session = user_sessions[user_id]

    if not session["can_recommend"]:
        raise HTTPException(status_code=402, detail="아직 책 추천이 불가능한 상태입니다. 더 많은 대화를 나눠주세요.")

    target_titles = set(session.get("recommended_titles", []))
    if not target_titles:
        raise HTTPException(status_code=400, detail="추천 도서가 존재하지 않습니다.")

    matched_books = [b for b in books if b["title"] in target_titles][:3]

    if not matched_books:
        raise HTTPException(status_code=400, detail="책 데이터에서 추천 도서를 찾을 수 없습니다.")

    recommendations = []
    for book in matched_books:
        keywords = [kw["word"] for kw in book.get("keywords", [])[:5]]
        recommendations.append({
            "bookTitle": book["title"],
            "bookReason": f"{', '.join(keywords)} 관련 주제",
            "imageUrl": book.get("imageUrl", ""),
            "bookUrl": book.get("bookUrl", ""),
            "bookSummary": book.get("summary", ""),
            "bookGenre": book.get("class_nm", "")
        })

    return {
        "recommendations": recommendations,
        "keywords": session["keywords"],
        "userType": session.get("user_type", "분석 중..."),
        "userTypeReason": session.get("user_type_reason", "분석 중...")
    }
