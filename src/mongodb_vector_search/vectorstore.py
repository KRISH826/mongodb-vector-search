from .embeddings import encode_model
from .db import get_collection

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
