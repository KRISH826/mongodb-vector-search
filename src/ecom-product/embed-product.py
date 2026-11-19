from functools import lru_cache
from itertools import batched
from typing import Any
from pymongo import UpdateOne
from sentence_transformers import SentenceTransformer

from .config.config import settings
from .db.db import get_db

DB_BATCH_SIZE = 2000
ENCODE_BATCH_SIZE = 512


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Model ko sirf ek baar RAM/GPU mein load karta hai (Singleton)."""
    print(f"Loading embedding model: {settings.embedding_model}...")
    return SentenceTransformer(settings.embedding_model)


def prepare_text_for_embedding(doc: dict[str, Any]) -> str:
    """Enriched semantic_text use karta hai (bina duplicate fields jode)."""
    if doc.get("semantic_text"):
        return str(doc["semantic_text"]).strip()

    # Fallback agar kisi doc par enrich-db nahi chala ho
    base_text = doc.get("search_text") or doc.get("name", "")
    gift_for = ", ".join(doc.get("gift_for", []))
    occasions = ", ".join(doc.get("occasions", []))

    extras = [
        f"Ideal gift for: {gift_for}." if gift_for else "",
        f"Occasions: {occasions}." if occasions else "",
    ]
    joined_extras = " ".join(e for e in extras if e)
    return f"{base_text} {joined_extras}".strip()


def generate_embeddings() -> None:
    db = get_db()
    model = get_embedding_model()

    query = {"embedding": {"$exists": False}}
    remaining = db["products"].count_documents(query)
    if remaining == 0:
        print("All products already embedded!")
        return

    projection = {
        "_id": 1,
        "name": 1,
        "search_text": 1,
        "semantic_text": 1,
        "gift_for": 1,
        "occasions": 1,
    }

    cursor = db["products"].find(query, projection).batch_size(DB_BATCH_SIZE)
    total_embedded = 0

    for batch in batched(cursor, DB_BATCH_SIZE):
        texts = [prepare_text_for_embedding(doc) for doc in batch]

        vectors = model.encode(
            texts,
            batch_size=ENCODE_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        ops = [
            UpdateOne(
                {"_id": doc["_id"]},
                {"$set": {"embedding": vec.tolist()}},
            )
            for doc, vec in zip(batch, vectors)
        ]

        if ops:
            db["products"].bulk_write(ops, ordered=False)
            total_embedded += len(ops)
            print(f"Embedded {total_embedded:,} / {remaining:,} successfully")

    print(f"Done! Total products embedded: {total_embedded:,}")


if __name__ == "__main__":
    generate_embeddings()