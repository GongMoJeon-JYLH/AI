from models.deepseek_lightrag import get_rag_instance
import asyncio
import os
import requests
import json
from dotenv import load_dotenv
from models.custom_kg_generator import generate_custom_kg_from_books  

load_dotenv()

BOOKS_JSON_PATH = "books_with_age.json"

# 📚 연령대별 인기 도서 수집 (초등~노년층까지 연령대별 수집)
def fetch_popular_books_all_ages():
    all_books = []
    seen = {}
    age_groups = [
        ("8-13", 8, 13),     # 초등학생
        ("14-16", 14, 16),   # 중학생
        ("17-19", 17, 19),   # 고등학생
        ("20-39", 20, 39),   # 20~30대
        ("40-59", 40, 59),   # 40~50대
        ("60-80", 60, 80)    # 60~80대
    ]

    for label, from_age, to_age in age_groups:
        print(f"📥 연령대 {label} 수집 중...")
        books_raw = fetch_popular_books(from_age=str(from_age), to_age=str(to_age), page_size=200)
        count = 0
        for item in books_raw:
            if count >= 120:
                break
            doc = item.get("doc", {})
            isbn = doc.get("isbn13")
            if not isbn:
                continue
            if isbn in seen:
                if label not in seen[isbn]["age"]:
                    seen[isbn]["age"].append(label)
                continue

            summary = fetch_summary_for_book(isbn)
            keywords = fetch_keywords_for_book(isbn)

            book_data = {
                "title": doc.get("bookname"),
                "authors": doc.get("authors"),
                "publisher": doc.get("publisher"),
                "publication_year": doc.get("publication_year"),
                'class_nm': doc.get('class_nm'),
                "isbn13": isbn,
                "summary": summary,
                "keywords": keywords,
                "imageUrl": doc.get("bookImageURL"),
                "bookUrl": doc.get("bookDtlUrl"),
                "age": [label]
            }
            seen[isbn] = book_data
            all_books.append(book_data)
            count += 1

        print(f"✅ {label} 연령대에서 {count}권 수집 완료.")

    return list(seen.values())

def fetch_popular_books(start_date="2023-01-01", end_date="2025-04-13", from_age="8", to_age="13", page_size=100):
    auth_key = os.getenv("DATA4LIBRARY_API_KEY")
    url = f"http://data4library.kr/api/loanItemSrch"
    params = {
        "authKey": auth_key,
        "startDt": start_date,
        "endDt": end_date,
        "from_age": from_age,
        "to_age": to_age,
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
    books = fetch_popular_books_all_ages()

    # 연령대별 통계
    from collections import defaultdict
    age_counts = defaultdict(int)
    for book in books:
        for age in book["age"]:
            age_counts[age] += 1

    print("\n📊 연령대별 수집된 책 수:")
    for age_range, count in age_counts.items():
        print(f" - {age_range}세: {count}권")

    with open(BOOKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    return books

FAILED_LOG_PATH = "failed_indices.json"

async def load_or_update_books_and_insert(rag, start_index: int = 0) -> list:
    if not os.path.exists(BOOKS_JSON_PATH):
        print("📚 데이터 파일이 없어 업데이트를 진행합니다...")
        books = update_book_data()
    else:
        print("✅ 기존 도서 데이터 로드 중...")
        with open(BOOKS_JSON_PATH, "r", encoding="utf-8") as f:
            books = json.load(f)

    # 실패 인덱스 불러오기
    if os.path.exists(FAILED_LOG_PATH):
        with open(FAILED_LOG_PATH, "r", encoding="utf-8") as f:
            failed_indices = set(json.load(f))
        print(f"⚠️ 이전 실패 인덱스 {len(failed_indices)}개 재시도 중...")
    else:
        failed_indices = None

    from services.book_formatter import format_book_json_with_weight
    docs = format_book_json_with_weight(BOOKS_JSON_PATH)

    failed = []

    for i, doc in enumerate(docs):
        if failed_indices is not None:
            if i not in failed_indices:
                continue
        elif i < start_index:
            continue

        try:
            await rag.ainsert(doc)
            print(f"✅ [{i}] insert 성공")
        except Exception as e:
            print(f"❌ [{i}] insert 실패: {e}")
            failed.append(i)

    if failed:
        with open(FAILED_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(failed, f, ensure_ascii=False, indent=2)
        print(f"📛 총 {len(failed)}개 실패 → {FAILED_LOG_PATH} 저장 완료.")
    elif os.path.exists(FAILED_LOG_PATH):
        os.remove(FAILED_LOG_PATH)
        print("🎉 모든 insert 성공 → 실패 로그 삭제됨.")

    # ✅ Custom KG 삽입
    print("📌 커스텀 Knowledge Graph 삽입 중...")
    custom_kg = await generate_custom_kg_from_books(BOOKS_JSON_PATH)
    await rag.ainsert_custom_kg(custom_kg)
    print("✅ 커스텀 KG 삽입 완료")

    return books

# 🔪 테스트 실행 시
if __name__ == "__main__":
    import asyncio

    async def test():
        rag = await get_rag_instance()
        books = await load_or_update_books_and_insert(rag,start_index=309)
        print(f"총 {len(books)}권의 책이 로드됨.")

    asyncio.run(test())
