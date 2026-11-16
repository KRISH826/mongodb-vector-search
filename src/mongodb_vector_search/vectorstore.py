from .embeddings import encode_model
from .db import get_collection

STOP_WORDS = {"what", "was", "is", "the", "of", "a", "an", "in", "for",
              "and", "to", "how", "much", "did", "does", "s"}

def keyword_query(query: str) -> str:
    words = query.replace("'", " ").replace("?", " ").split()
    return " ".join(w for w in words if w.lower() not in STOP_WORDS)              

def search(query: str, k:int = 5):
    query_vector = encode_model(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": k,
            }
        },
        {
            "$project": {
                "_id": 0,
                # Documents currently store their chunk content under "texts".
                # Expose it as "text" so callers have a consistent result shape.
                "text": "$texts",
                "source_file": 1,
                "page": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    return list(get_collection().aggregate(pipeline))


def keyword_search(query: str, k: int = 5):
    pipeline = [
        {
            "$search": {
                "index": "text_index",
                "text": {"query": query, "path": "texts"},
            }
        },
        {"$limit": k},
        {
            "$project": {
                "_id": 0,
                "text": "$texts",
                "source_file": 1,
                "page": 1,
                "score": {"$meta": "searchScore"},
            }
        },
    ]
    return list(get_collection().aggregate(pipeline))


def hybrid_search(query: str, k:int = 5):
    vec = search(query, 20)
    kw = keyword_search(keyword_query(query), 20)

    # types
    scores: dict[tuple, float] = {}
    docs: dict[tuple, dict] = {}

    for result in (vec, kw):
        for rank, c in enumerate(result):
            key = (c["source_file"], c["page"], c["text"][:50])
            docs[key] = c
            scores[key] = scores.get(key, 0) + 1 / (60 + rank)

    best = sorted(scores, key=lambda key: scores[key], reverse=True)[:k]
    return [{**docs[key], "score": scores[key]} for key in best]