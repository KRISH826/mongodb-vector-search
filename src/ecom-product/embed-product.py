from functools import lru_cache
from itertools import batched
from typing import Any
from pymongo import UpdateOne
from sentence_transformers import SentenceTransformer
from .config.config import settings
from .db.db import get_db

ENCODE_BATCH_SIZE = 128


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Model ko sirf ek baar RAM/GPU mein load karta hai (Singleton)."""
    print(f"Loading embedding model: {settings.embedding_model}...")
    return SentenceTransformer(settings.embedding_model)

def prepare_text_for_embedding(doc: dict[str, Any]) -> str:
    """"
    Existing Field (search_text, semantic_text, gift_for, ocassion, season)
    
    """

    base_text = doc.get("semantic_text") or doc.get("search_text") or doc.get("name", "")
    gift_for = ", ".join(doc.get("gift_for", []))
    occasions = ", ".join(doc.get("occasions", []))

    extras = [
        f"Ideal gift for: {gift_for}." if gift_for else "",
        f"Occasions: {occasions}." if occasions else "",
    ]

    return f"{base_text} {", ".join(e for e in extras if e)}".strip()


def generate_embeddings():
    db = get_db()
    model = get_embedding_model()

    query = {"embedding": {"$exists": False}}
    projection = {
        "_id": 1,
        "name": 1,
        "search_text": 1,
        "semantic_text": 1,
        "gift_for": 1,
        "occasions": 1,
    }

    cursor = db["products"].find(query, projection).batch_size(ENCODE_BATCH_SIZE)
    total_embedded = 0

    for batch in batched(cursor, ENCODE_BATCH_SIZE):
        texts = [prepare_text_for_embedding(doc) for doc in batch]

        vectors = model.encode(
            texts,
            batch_size= ENCODE_BATCH_SIZE,
            normalize_embeddings= True,
            show_progress_bar= True
        )

        ops = [
            UpdateOne(
                {"_id": doc["_id"]},
                {"$set": {"embedding": vec.tolist()}},
            )
            for doc, vec in vectors
        ]

        if ops:
            db["products"].bulk_write(ops, ordered=False)
            total_embedded += len(ops)
            print(f"Embedded {total_embedded} successfully")

    print(f"Done! Total products embedded: {total_embedded:,}")

if __name__ == "__main__":
    generate_embeddings()     