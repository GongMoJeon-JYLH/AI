from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from services.book_updater import load_or_update_books
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4

app = FastAPI(
    title="더미 도서 추천 API",
    description="사용자의 입력에서 관심 키워드를 추출하고, 더미 도서 데이터 중 유사한 책을 추천합니다.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 더미 도서 데이터
books, vector = load_or_update_books()
users = {}

# ====================== 모델 ======================
class UserName(BaseModel):
    name: str

class Userinfo(BaseModel):
    name: str
    userId: str

class UserMessage(BaseModel):
    userMessage: str
    userId: str

class ChatResponse(BaseModel):
    responseText: str
    canRecommend: bool

class BookRecommendation(BaseModel):
    bookTitle: str
    bookReason: str
    imageUrl: str
    bookUrl: str
    bookSummary: str
    bookGenre: str

class BookRecommendationList(BaseModel):
    recommendations: List[BookRecommendation]

# ====================== 유틸 ======================
def extract_keywords_mock(text: str) -> List[str]:
    if "스트레스" in text or "우울" in text:
        return ["스트레스", "감정"]
    elif "역사" in text:
        return ["중학생", "역사"]
    elif "사회" in text:
        return ["사회", "문제의식"]
    else:
        return ["중학생", "책"]

def get_embedding_from_keywords(keywords: List[str]) -> List[float]:
    keyword_map = {
        "역사": [0.1, 0.2, 0.3, 0.4],
        "감정": [0.05, 0.1, 0.2, 0.3],
        "스트레스": [0.05, 0.1, 0.2, 0.3],
        "사회": [0.4, 0.3, 0.2, 0.1],
        "문제의식": [0.35, 0.3, 0.2, 0.1],
        "중학생": [0.2, 0.2, 0.2, 0.2],
        "책": [0.1, 0.1, 0.1, 0.1]
    }
    vectors = [keyword_map.get(k, [0.0, 0.0, 0.0, 0.0]) for k in keywords]
    return list(np.mean(vectors, axis=0))
# ====================== API ======================
@app.post("/users", tags=["유저 ID 생성"], response_model=Userinfo)
def createUser(userName: UserName):
    if not userName.name or userName.name.strip() == "":
        raise HTTPException(status_code=400, detail="유저 이름이 비어있습니다.")
    
    userId = str(uuid4())
    print(userName.name, userId)
    users[userName.name] = userId
    return {"name": userName.name, "userId": userId}

@app.post("/chat", tags=["채팅"], response_model=ChatResponse)
def chat(message: UserMessage):
    return {"responseText": f"어떤 장르를 좋아하시나요?", "canRecommend": True}

@app.post("/book-recommend", tags=["도서 추천"], response_model=BookRecommendationList)
def bookRecommend(userinfo: Userinfo):
    top_books = books[:3]
    recommendations = []
    for book in top_books:
        book_keywords = [kw["word"] for kw in book['keywords'][:5]]
        recommendations.append({
            "bookTitle": book["title"],
            "bookReason": f"{', '.join(book_keywords)} 관련 주제",
            "imageUrl": book["imageUrl"],
            "bookUrl": book["bookUrl"],
            "bookSummary":book["summary"],
            "bookGenre": book["class_nm"]
        })

    return {"recommendations": recommendations}
