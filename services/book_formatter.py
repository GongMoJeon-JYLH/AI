import json
def format_book_json_with_weight(json_path: str) -> list:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    docs = []
    for book in data:
        title = book.get("title", "")
        summary = book.get("summary", "")
        class_nm = book.get("class_nm", "")
        age = book.get("age", [])
        keywords_raw = book.get("keywords", [])

        weighted_keywords = []
        for kw in keywords_raw:
            word = kw["word"]
            weight = int(kw["weight"])
            weighted_keywords.extend([word] * weight)

        doc_obj = {
            "title": title,
            "category": class_nm,
            "summary": summary,
            "keywords": weighted_keywords,
            "age_group": age
        }

        docs.append(json.dumps(doc_obj, ensure_ascii=False))
    return docs
