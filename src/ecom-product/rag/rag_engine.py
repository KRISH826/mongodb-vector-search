import os
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from typing import Any
from sentence_transformers import SentenceTransformer

from ..config.config import settings
from ..db.db import get_db

_model: SentenceTransformer | None = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)

    return _model

class SearchInput(BaseModel):
    semantic_query: str = Field(
        ...,
        description="Clean product search intent (e.g., 'high performance gaming smartphone' or 'thoughtful gift for sister')",
    )

    max_price: float | None = Field(
        default=None,
        description="Maximum budget in INR if mentioned by user, else None",
    )
    gift_for: str | None = Field(
        default=None,
        description="Recipient in lowercase if gift mentioned (e.g., 'sister', 'brother', 'mother'), else None",
    )
    occasion: str | None = Field(
        default=None,
        description="Occasion in lowercase if mentioned (e.g., 'bhaidooj', 'diwali', 'birthday'), else None",
    )


def extract_intent(user_query:str) -> SearchInput:
    """
    User ki natural query se structured filters + semantic query nikaalta hai using Groq (Llama 3.3 70B).
    """

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try: 
            llm = ChatGroq(
                model="openai/gpt-oss-120b",
                temperature=0,
                max_retries=2,
            )
            structured_llm = llm.with_structured_output(SearchInput, method="json_mode")
            prompt = (
                "Extract e-commerce search parameters from the user's query. "
                "Keep 'semantic_query' rich in product attributes and use-cases. "
                "Normalize 'gift_for' and 'occasion' to lowercase single words if present (e.g., 'sister', 'bhaidooj').\n\n"
                f"User Query: {user_query}"
            )

            return SearchInput.model_validate(structured_llm.invoke(prompt))
        except Exception as e:
            print(f"[Warning] Groq intent extraction fallback triggered: {e}")

    return SearchInput(semantic_query=user_query)

def build_pre_filter(intent: SearchInput) -> dict[str, Any]:
    """MongoDB Atlas $vectorSearch ke liye valid pre-filter dictionary banata hai."""

    conditions: list[dict[str, Any]] = [
        {"is_active": {"$eq": True}},
        {"stock": {"$gt": 0}},
    ]

    if intent.max_price is not None:
        conditions.append({"price.selling_price": {"$lte": intent.max_price}})

    if intent.gift_for:
        conditions.append({"gift_for": {"$in": [intent.gift_for.lower()]}})

    if intent.occasion:
        conditions.append({"occasions": {"$in": [intent.occasion.lower()]}})

    return {"$and": conditions} if len(conditions) > 1 else conditions[0]    


def hybrid_product_search(user_query: str, limit: int = 5) -> dict[str, Any]:
    """
    Complete Hybrid Search Pipeline:
    1. Intent Extraction -> 2. Query Embedding -> 3. Atlas $vectorSearch -> 4. Clean Results
    """

    db = get_db()
    model = get_model()

    intent = extract_intent(user_query)

    query_vector = model.encode(
        intent.semantic_query, normalize_embeddings= True
    ).tolist()

    pre_filter = build_pre_filter(intent)

    pipeline = [
        {
            "$vectorSearch": {
                "index": settings.vector_index_name,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": limit * 20,  # HNSW graph mein 100 candidates scan honge
                "limit": limit,
                "filter": pre_filter,
            }
        },

        {
            "$project": {
                "_id": 1,
                "name": 1,
                "price": 1,
                "gift_for": 1,
                "occasions": 1,
                "rating": 1,
                "search_text": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        }
    ]

    results = list(db["products"].aggregate(pipeline))

    # Fallback: Agar strict gift_for/occasion filter se 0 results aayein, toh sirf price + stock filter par pure semantic search chalao
    if not results and (intent.gift_for or intent.occasion):
        fallback_conditions: list[dict[str, Any]] = [
            {"is_active": {"$eq": True}},
            {"stock": {"$gt": 0}},
        ]
        if intent.max_price is not None:
            fallback_conditions.append({"price.selling_price": {"$lte": intent.max_price}})

        pipeline[0]["$vectorSearch"]["filter"] = {"$and": fallback_conditions}
        results = list(db["products"].aggregate(pipeline))

    return {
        "user_query": user_query,
        "extracted_intent": intent.model_dump(),
        "total_found": len(results),
        "products": results,
    }

if __name__ == "__main__":
    test_queries = [
        "behen ke liye bhaidooj pe badhiya gift dikhao 5000 ke andar",
        "bhai gaming ke liye ek tagda phone suggest kar 30000 tak",
    ]

    for q in test_queries:
        print(f"QUERY: {q}")
        response = hybrid_product_search(q, limit=3)
        print(response)

