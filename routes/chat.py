# routes/chat_mock.py
from fastapi import APIRouter
from models.schemas import UserMessage, Userinfo
from typing import List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

router = APIRouter()

books_db = [
    {
        "title": "더러워: 냄새나는 세계사",
        "grade": "중1",
        "keywords": ["역사", "위생", "문화"],
        "embedding": [0.1, 0.2, 0.3, 0.4],
        "summary": "고대부터 현대까지 위생과 문명의 변화를 보여주는 책",
        "imageUrl": "https://example.com/image1.jpg",
        "bookUrl": "https://library.example.com/book1"
    },
    {
        "title": "십 대를 위한 마음 수업",
        "grade": "중2",
        "keywords": ["감정", "스트레스", "자존감"],
        "embedding": [0.05, 0.1, 0.2, 0.3],
        "summary": "십 대의 감정과 고민을 따뜻하게 다룬 책",
        "imageUrl": "https://example.com/image2.jpg",
        "bookUrl": "https://library.example.com/book2"
    },
    {
        "title": "세상은 어떻게 돌아가는가",
        "grade": "중3",
        "keywords": ["사회", "정치", "문제의식"],
        "embedding": [0.4, 0.3, 0.2, 0.1],
        "summary": "세상의 구조와 문제를 생각하게 하는 책",
        "imageUrl": "https://example.com/image3.jpg",
        "bookUrl": "https://library.example.com/book3"
    },
]

# 간단한 키워드 추출 mock 함수
def extract_keywords_mock(text: str) -> List[str]:
    if "스트레스" in text or "우울" in text:
        return ["스트레스", "감정"]
    elif "역사" in text:
        return ["중학생", "역사"]
    elif "사회" in text:
        return ["사회", "문제의식"]
    else:
        return ["중학생", "책"]

# 키워드를 임베딩하는 mock 함수
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

@router.post("/chat")
def chat(message: UserMessage):
    keywords = extract_keywords_mock(message.userMessage)
    return {"responseText": f"당신의 관심 키워드는 {', '.join(keywords)} 입니다."}
