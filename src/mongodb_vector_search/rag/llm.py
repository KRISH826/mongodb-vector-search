from langchain_deepseek import ChatDeepSeek
from functools import lru_cache
from ..config import settings


@lru_cache
def get_llm():
    return ChatDeepSeek(
        model= 'deepseek-v4-pro',
        temperature= 0,
        api_key= settings.deepseek_api_key # type: ignore
    )