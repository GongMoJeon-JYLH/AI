import os
import requests
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

BOOKS_JSON_PATH = "books_keywords.json"
BOOKS_VECTOR_PATH = "books_keywords_vectors.npy"

model = SentenceTransformer("jhgan/ko-sbert-nli")

def fetch_popular_books(start_date="2023-01-01", end_date="2025-04-13", age="10", page_size=100):
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
    items = data.get("response", {}).get("items", [])
    return [
        {"word": item["item"]["word"], "weight": int(item["item"]["weight"])}
        for item in items if "item" in item
    ]

def fetch_summary_for_book(isbn13: str) -> list:
    auth_key = os.getenv("DATA4LIBRARY_API_KEY")
    url = f"http://data4library.kr/api/srchDtlList"
    params = {
        "authKey": auth_key,
        "isbn13": isbn13,
        "loaninfo": "Y",
        "format": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    try:
        return data["response"]["detail"][0]["book"]["description"]
    except (KeyError, IndexError):
        return ""
def update_book_data():
    books_raw = fetch_popular_books()
    books = []
    for item in books_raw:
        doc = item["doc"]
        isbn = doc.get("isbn13")
        if not isbn:
            continue
        
        summary = fetch_summary_for_book(isbn)
        keywords = fetch_keywords_for_book(isbn)
        books.append({
            "title": doc.get("bookname"),
            "authors": doc.get("authors"),
            "publisher": doc.get("publisher"),
            "publication_year": doc.get("publication_year"),
            'class_nm': doc.get('class_nm'),
            "isbn13": isbn,
            "summary": summary,
            "keywords": keywords,
            "imageUrl": doc.get("bookImageURL"),
            "bookUrl": doc.get("bookDtlUrl")
        })

    with open(BOOKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    texts = [f"{b['title']} {b['summary']} {' '.join([kw['word'] for kw in b['keywords']])}" for b in books]
    vectors = model.encode(texts)
    np.save(BOOKS_VECTOR_PATH, vectors)

    return books, vectors

def load_or_update_books():
    """books_keywords.json 또는 벡터 파일이 없으면 자동 생성"""
    if not os.path.exists(BOOKS_JSON_PATH) or not os.path.exists(BOOKS_VECTOR_PATH):
        print("📚 데이터 파일이 없어 업데이트를 진행합니다...")
        return update_book_data()
    else:
        print("✅ 기존 도서 데이터 로드 중...")
        with open(BOOKS_JSON_PATH, "r", encoding="utf-8") as f:
            books = json.load(f)
        vectors = np.load(BOOKS_VECTOR_PATH)
        return books, vectors

# 🧪 테스트 실행 시
if __name__ == "__main__":
    books, vectors = load_or_update_books()
    print(f"총 {len(books)}권의 책이 로드됨.")