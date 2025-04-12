from fastapi import APIRouter
from models.schemas import Query
from services.book_loader import load_books, load_vectors, model
from services.book_updater import update_books_from_api
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

router = APIRouter()

books = load_books()
book_vectors = load_vectors()

@router.post("/recommend")
def recommend_book(query: Query):
    global books, book_vectors

    if not books or book_vectors is None:
        return {"error": "도서 데이터가 비어 있습니다."}

    query_vector = model.encode([query.question])
    similarities = cosine_similarity(query_vector, book_vectors)[0]

    top_indices = np.argsort(similarities)[::-1][:3]
    recommendations = []
    for idx in top_indices:
        doc = books[idx]
        recommendations.append({
            "bookTitle": doc["title"],
            "bookReason": f"{', '.join(doc['keywords'])} 관련 주제",
            "imageUrl": doc["imageUrl"],
            "bookUrl": doc["bookUrl"]
        })
    return {"recommendations": recommendations}

@router.post("/update-books")
def update_books():
    global books, book_vectors
    books, book_vectors = update_books_from_api()
    return {"message": "도서 데이터와 벡터가 업데이트되었습니다.", "count": len(books)}