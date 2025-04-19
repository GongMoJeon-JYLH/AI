# services/session_store.py

from collections import defaultdict

user_sessions = defaultdict(lambda: {
    "messages": [],              # 사용자 메시지 기록
    "keywords": [],              # 추출된 키워드
    "can_recommend": False,      # 추천 가능 여부
    "recommended_titles": []     # 추천된 책 제목 저장
})