
from sentence_transformers import SentenceTransformer
from ..config.config import settings


def get_embedding_model() -> SentenceTransformer:
    """Model ko sirf ek baar RAM/GPU mein load karta hai (Singleton)."""
    print(f"Loading embedding model: {settings.embedding_model}...")
    return SentenceTransformer(settings.embedding_model)