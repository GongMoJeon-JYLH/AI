import json

async def generate_custom_kg_from_books(json_path: str) -> dict: 
    with open(json_path, "r", encoding="utf-8") as f: books = json.load(f)

    chunks, entities, relationships = [], [], []

    for idx, book in enumerate(books):
        book_id = f"book-{idx}"
        title = book.get("title", "")
        summary = book.get("summary", "")
        authors = book.get("authors", "")
        isbn = book.get("isbn13", "")
        keywords = [kw["word"] for kw in book.get("keywords", [])]
        age = ", ".join(book.get("age", []))

        # 📘 Chunk (책 내용 요약)
        chunks.append({
            "content": f"{title} - {summary}",
            "source_id": book_id
        })

        # 🧠 Entities
        entities.append({
            "entity_name": title,
            "entity_type": "book",
            "description": summary,
            "source_id": book_id
        })

        if isbn:
            entities.append({
                "entity_name": isbn,
                "entity_type": "isbn13",
                "description": f"{title}의 고유 ISBN",
                "source_id": book_id
            })

        if authors:
            entities.append({
                "entity_name": authors,
                "entity_type": "author",
                "description": f"{title}의 저자",
                "source_id": book_id
            })

        for kw in keywords[:10]:
            entities.append({
                "entity_name": kw,
                "entity_type": "keyword",
                "description": f"{title}과 관련된 키워드",
                "source_id": book_id
            })

        if authors:
            relationships.append({
                "src_id": title,
                "tgt_id": authors,
                "description": f"{authors}는 {title}의 저자입니다.",
                "keywords": "저자",
                "weight": 1.0,
                "source_id": book_id
            })

        if isbn:
            relationships.append({
                "src_id": title,
                "tgt_id": isbn,
                "description": f"{title}의 ISBN은 {isbn}입니다.",
                "keywords": "식별자",
                "weight": 1.0,
                "source_id": book_id
            })

        for kw in keywords[:10]:
            relationships.append({
                "src_id": title,
                "tgt_id": kw,
                "description": f"{title}은(는) '{kw}'와 관련된 책입니다.",
                "keywords": "주제 키워드",
                "weight": 0.8,
                "source_id": book_id
            })
        
        for age_group in book.get("age", []):
            entities.append({
                "entity_name": age_group,
                "entity_type": "age_group",
                "description": f"{title}의 주요 인기 연령대: {age_group}",
                "source_id": book_id
            })
            relationships.append({
                "src_id": title,
                "tgt_id": age_group,
                "description": f"{title}은(는) {age_group} 연령대에서 인기가 많습니다.",
                "keywords": "인기 연령대",
                "weight": 0.7,
                "source_id": book_id
            })

    return {
        "chunks": chunks,
        "entities": entities,
        "relationships": relationships
    }
