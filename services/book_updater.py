import os
import requests
import json
import numpy as np
from sentence_transformers import SentenceTransformer

BOOKS_JSON_PATH = "books_keywords.json"
BOOKS_VECTOR_PATH = "books_keywords_vectors.npy"

model = SentenceTransformer("jhgan/ko-sbert-nli")

def fetch_popular_books(start_date="2023-01-01", end_date="2023-12-31", age="10", page_size=100):
    auth_key = os.getenv("DATA4LIBRARY_API_KEY")
    url = f"http://data4library.kr/api/loanItemSrch"
    params = {
        "authKey": auth_key,
        "startDt": start_date,
        "endDt": end_date,
        "age": age,
        "pageSize": page_size,
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("response", {}).get("docs", [])

def fetch_keywords_for_book(isbn13: str) -> list:
    auth_key = os.getenv("DATA4LIBRARY_API_KEY")
    url = f"http://data4library.kr/api/keywordList"
    params = {
        "authKey": auth_key,
        "isbn13": isbn13,
        "additionalYN": "Y",
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    words = data.get("keywords", {}).get("item", [])
    return [w["word"] for w in words] if isinstance(words, list) else []

def update_book_data():
    books_raw = fetch_popular_books()
    books = []
    for item in books_raw:
        doc = item["doc"]
        isbn = doc.get("isbn13")
        if not isbn:
            continue

        keywords = fetch_keywords_for_book(isbn)
        books.append({
            "title": doc.get("bookname"),
            "authors": doc.get("authors"),
            "publisher": doc.get("publisher"),
            "publication_year": doc.get("publication_year"),
            "isbn13": isbn,
            "summary": f"{doc.get('authors')} / {doc.get('publisher')} ({doc.get('publication_year')})",
            "keywords": keywords,
            "imageUrl": doc.get("bookImageURL"),
            "bookUrl": doc.get("bookDtlUrl")
        })

    with open(BOOKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    texts = [f"{b['title']} {b['summary']} {' '.join(b['keywords'])}" for b in books]
    vectors = model.encode(texts)
    np.save(BOOKS_VECTOR_PATH, vectors)

    return books, vectors
