from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re
from services.book_searcher import search_books

# 모델 로딩
tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/deepseek-llm-7b-chat", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/deepseek-llm-7b-chat",
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)

def generate_chat_response(messages: list[str], max_tokens=512):
    prompt = "<|system|>\n너는 사용자에게 책을 추천해주는 친절한 챗봇이야.\n"
    for i, m in enumerate(messages):
        role = "<|user|>" if i % 2 == 0 else "<|assistant|>"
        prompt += f"{role}\n{m}\n"
    prompt += "<|assistant|>\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=max_tokens)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return result.split("<|assistant|>")[-1].strip()

def extract_search_keywords(output: str):
    match = re.search(r"search_books\(\"(.*?)\"\)", output)
    return match.group(1) if match else None

def full_recommendation_conversation(user_input: str):
    messages = [user_input]
    first_response = generate_chat_response(messages)
    print("🤖 1차 응답:", first_response)

    # 벡터 검색 키워드 감지
    keywords = extract_search_keywords(first_response)
    if not keywords:
        return first_response

    # 유사한 책 검색
    found_books = search_books(keywords)
    book_info = "\n".join([f"- {b['title']}: {b['summary']}" for b in found_books])

    # 추천 책 목록 전달 + 응답 생성
    messages.extend([first_response, f"검색된 책 목록은 다음과 같아요:\n{book_info}\n어떤 책이 좋을까요?"])
    final_response = generate_chat_response(messages)
    return final_response

if __name__ == "__main__":
    user_input = input("당신의 고민이나 관심사를 입력해주세요: ")
    final = full_recommendation_conversation(user_input)
    print("\n📚 최종 추천 답변:\n", final)