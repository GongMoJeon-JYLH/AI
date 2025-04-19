import json

def format_book_json_with_weight(json_path: str) -> list:
    """
    JSON 파일을 불러와 title, summary, class_nm, 키워드(weight 반영)를 포함한 리스트 형태로 리턴합니다.

    Args:
        json_path (str): 입력 JSON 경로
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    docs = []
    for book in data:
        title = book.get("title", "")
        summary = book.get("summary", "")
        class_nm = book.get("class_nm", "")
        keywords_raw = book.get("keywords", [])
        
        weighted_keywords = []
        for kw in keywords_raw:
            word = kw["word"]
            weight = int(kw["weight"])
            weighted_keywords.extend([word] * weight)

        keywords_str = " ".join(weighted_keywords)

        content = (
            f"제목: {title}\n"
            f"분류: {class_nm}\n"
            f"요약: {summary}\n"
            f"키워드: {keywords_str}"
        )
        docs.append(content)
    return docs