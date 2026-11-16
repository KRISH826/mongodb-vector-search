from langchain_deepseek import ChatDeepSeek
from functools import lru_cache
from ..config import settings


@lru_cache
def get_llm(model, temperature: float = 0.0, max_tokens: int = 2048):
    return ChatDeepSeek(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.deepseek_api_key,  # type: ignore
    )
