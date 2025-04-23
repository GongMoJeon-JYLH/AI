import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import EmbeddingFunc
from services.book_formatter import format_book_json_with_weight
from dotenv import load_dotenv
import numpy as np

load_dotenv()

WORKING_DIR = "./rag_working_dir3"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
    from lightrag.llm.openai import openai_complete_if_cache
    
    return await openai_complete_if_cache(
        model="deepseek-chat",
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        base_url="https://api.deepseek.com/v1",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        **kwargs
    )

# Embedding: OpenAI
async def embedding_func(texts: list[str]) -> np.ndarray:
    from lightrag.llm.openai import openai_embed

    return await openai_embed(
        texts,
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://api.openai.com/v1"
    )

# LightRAG 초기화
async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,  # OpenAI text-embedding-3-small 기준
            max_token_size=8192,
            func=embedding_func
        )
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag

_rag_instance = None

async def get_rag_instance():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = await initialize_rag()
    return _rag_instance

def main():
    # Initialize RAG instance
    rag = asyncio.run(initialize_rag())

    books = format_book_json_with_weight('./books_keywords.json')
    for book in books:
        rag.insert(book)

    print(
        rag.query(
            "흔한 남매 책 중에 추천해줘", param=QueryParam(mode="hybrid")
        )
    )
if __name__ == "__main__":
    main()