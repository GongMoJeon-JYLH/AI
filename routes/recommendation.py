# routes/book_recommend.py
from fastapi import APIRouter
from pydantic import BaseModel
import json
from services.session_store import user_sessions

BOOKS_JSON_PATH = "./books_keywords.json"
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

@router.post("/book-recommend", response_model=BookRecommendationList)
def book_recommend(userinfo: Userinfo):
    user_id = userinfo.userId
    if user_id not in user_sessions or not user_sessions[user_id]["recommended_titles"]:
        return {"recommendations": []}

    target_titles = set(user_sessions[user_id]["recommended_titles"])
    matched_books = [b for b in books if b["title"] in target_titles][:3]

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

    return {"recommendations": recommendations}
