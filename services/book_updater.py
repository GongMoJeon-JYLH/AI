import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

BOOKS_JSON_PATH = "books_keywords.json"

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

def fetch_summary_for_book(isbn13: str) -> str:
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

    return books

def load_or_update_books_and_insert(rag) -> list:
    """
    책 데이터를 로드하거나 없으면 업데이트 + rag.insert 실행까지
    """
    if not os.path.exists(BOOKS_JSON_PATH):
        print("📚 데이터 파일이 없어 업데이트를 진행합니다...")
        books = update_book_data()
    else:
        print("✅ 기존 도서 데이터 로드 중...")
        with open(BOOKS_JSON_PATH, "r", encoding="utf-8") as f:
            books = json.load(f)

    from services.book_formatter import format_book_json_with_weight
    docs = format_book_json_with_weight(BOOKS_JSON_PATH)

    for doc in docs:
        rag.insert(doc)

    return books

# 🔪 테스트 실행 시
if __name__ == "__main__":
    from models.deepseek_lightrag import get_rag
    import asyncio

    async def test():
        rag = await get_rag()
        books = load_or_update_books_and_insert(rag)
        print(f"총 {len(books)}권의 책이 로드됨.")

    asyncio.run(test())
