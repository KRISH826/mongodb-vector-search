from functools import lru_cache
from sentence_transformers import SentenceTransformer
from .config import settings

@lru_cache
def get_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)

def encode_model(text:str) -> list[float]:
    return get_model().encode(text).tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, batch_size=32).tolist()


