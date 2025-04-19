import os
from typing import List
import httpx
from dotenv import load_dotenv

load_dotenv()

# ✅ GPT로부터 키워드를 추출하는 함수
async def extract_keywords_from_gpt(user_message: str) -> List[str]:
    """
    사용자의 입력에서 키워드를 GPT를 통해 추출합니다.
    :param user_message: 사용자 발화
    :return: 키워드 리스트
    """
    system_prompt = """
        너는 사용자 입력으로부터 핵심 키워드를 추출하는 AI 비서야.
        사용자의 감정, 관심사, 상황을 반영하는 명사(또는 고유명사)를 최대 5개까지 골라줘.
        형용사나 동사, 문장 전체는 제거하고, 꼭 ‘명사’만 골라줘.

        아래 형식으로만 응답해줘:
        {"keywords": ["키워드1", "키워드2", "키워드3"]}

        예시:
        입력: "요즘 중학생 딸이 학교에서 왕따를 당해서 마음이 아파요."
        출력: {"keywords": ["중학생", "딸", "학교", "왕따", "마음"]}

        입력: "사회 문제에 관심 많은 고등학생인데 환경이나 인권 쪽 책이 좋아요"
        출력: {"keywords": ["사회 문제", "고등학생", "환경", "인권", "책"]}

        지금부터 사용자 입력을 줄게. 위 형식으로만 응답해줘.
        """


    # 🧠 deepseek-chat 또는 gpt-4o, gpt-3.5-turbo 등 가능
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = "https://api.openai.com/v1"  # DeepSeek일 경우: https://api.deepseek.com/v1
    model = "gpt-3.5-turbo"  # 또는 deepseek-chat

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.5
            }
        )

    result = response.json()
    try:
        content = result["choices"][0]["message"]["content"]
        keyword_data = eval(content)  # 단순 JSON 파싱
        return keyword_data.get("keywords", [])
    except Exception as e:
        print("❗키워드 추출 실패:", e)
        return []
