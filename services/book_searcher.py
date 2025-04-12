import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

BOOKS_JSON_PATH = "books_keywords.json"
BOOKS_VECTOR_PATH = "books_keywords_vectors.npy"

model = SentenceTransformer("jhgan/ko-sbert-nli")

# 데이터 로딩
with open(BOOKS_JSON_PATH, "r", encoding="utf-8") as f:
    books = json.load(f)
book_vectors = np.load(BOOKS_VECTOR_PATH)

def search_books(query: str, top_k: int = 3):
    query_vector = model.encode([query])
    similarities = cosine_similarity(query_vector, book_vectors)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        book = books[idx]
        results.append({
            "title": book["title"],
            "summary": book["summary"],
            "keywords": book.get("keywords", []),
            "imageUrl": book.get("imageUrl"),
            "bookUrl": book.get("bookUrl")
        })
    return results
