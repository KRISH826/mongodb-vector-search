import os
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field, field_validator
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

    style: str | None = Field(
        default=None,
        description="Product style in lowercase if mentioned (e.g., 'casual', 'formal', 'ethnic-casual', 'premium'), else None",
    )
    season: str | None = Field(
        default=None,
        description="Season in lowercase if mentioned (e.g., 'summer', 'winter', 'all-season'), else None",
    )
    vibe_keywords: list[str] = Field(
        default_factory=list,
        description="2-4 lowercase vibe or feature keywords (e.g., ['gaming', '5g', 'camera-phone']), else []",
    )

    @field_validator("vibe_keywords", mode="before")
    @classmethod
    def clean_vibe_keywords(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.split(",")
        if not isinstance(v, list):
            return []
        return [str(item).strip().lower() for item in v if str(item).strip()]
    gender = None


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
                "Extract e-commerce search parameters from the user's query (English, Hindi, or Hinglish) "
                "and respond ONLY with a valid JSON object matching this exact schema:\n"
                "{\n"
                '  "semantic_query": string,\n'
                '  "max_price": number or null,\n'
                '  "gender": "male" | "female" | "unisex" or null,\n'
                '  "gift_for": string or null,\n'
                '  "occasion": string or null,\n'
                '  "style": string or null,\n'
                '  "season": string or null,\n'
                '  "vibe_keywords": [string]\n'
                "}\n\n"
                "Rules:\n"
                "- Keep 'semantic_query' in rich English product attributes and use-cases.\n"
                "- Infer 'gender' strictly when recipient/user gender is clear "
                "(wife, girlfriend, mother, sister, behen, women -> 'female'; "
                "husband, boyfriend, father, brother, bhai, men -> 'male'). Otherwise null.\n"
                "- Normalize 'gift_for', 'occasion', 'style', 'season' to lowercase single words if present.\n"
                "- Extract 2-4 lowercase feature/vibe words in 'vibe_keywords' if applicable.\n\n"
                f"User Query: {user_query}"
            )

            raw_output = SearchInput.model_validate(structured_llm.invoke(prompt))
            return (
                raw_output
                if isinstance(raw_output, SearchInput)
                else SearchInput.model_validate(raw_output)
            )
        except Exception as e:
            print(f"[Warning] Groq intent extraction fallback triggered: {e}")

    return SearchInput(semantic_query=user_query)

def _gender_variants(gender: str) -> list[str]:
    """Gender ke saath unisex allow karta hai + DB ki mixed casing handle karta hai."""
    if gender == "female":
        return ["female", "unisex", "FEMALE", "UNISEX", "Female", "Unisex"]
    if gender == "male":
        return ["male", "unisex", "MALE", "UNISEX", "Male", "Unisex"]
    return ["unisex", "UNISEX", "Unisex"]

def _case_variants(value: str) -> list[str]:
    return list({value.lower(), value.title(), value.upper()})


def build_pre_filter(intent: SearchInput, tier: int = 1) -> dict[str, Any]:
    """MongoDB Atlas $vectorSearch ke liye valid pre-filter dictionary banata hai."""

    conditions:list[dict[str, Any]] = [
        {"is_active": {"$eq": True}},
        {"stock": {"$gt": 0}},
    ]

    if intent.max_price is not None:
        conditions.append({"price.selling_price": {"$lte": intent.max_price}})

    if tier in (1, 2) and intent.gender:
        conditions.append({"intent.gender": {"$in": _gender_variants(intent.gender)}})

    if tier == 1:
        if intent.gift_for:
            conditions.append({"gift_for": {"$in": _case_variants(intent.gift_for)}})
        if intent.occasion:
            conditions.append({"occasions": {"$in": _case_variants(intent.occasion)}})

    
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

