import os
from typing import Any, Literal
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field, field_validator
from sentence_transformers import SentenceTransformer
from pydantic import SecretStr
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
    gender: Literal["male", "female", "unisex"] | None = Field(
        default=None,
        description="Target gender inferred from query (e.g., wife/sister -> 'female', husband/brother -> 'male'), else None",
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

    @field_validator("gender", "gift_for", "occasion", "style", "season", mode="before")
    @classmethod
    def normalize_strings(cls, v: Any) -> str | None:
        if v is None or not str(v).strip():
            return None
        return str(v).strip().lower()

    @field_validator("vibe_keywords", mode="before")
    @classmethod
    def clean_vibe_keywords(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.split(",")
        if not isinstance(v, list):
            return []
        return [str(item).strip().lower() for item in v if str(item).strip()]


def extract_intent(user_query: str) -> SearchInput:

    if settings.groq_api_key:
        try:
            llm = ChatGroq(
                api_key=SecretStr(settings.groq_api_key),
                model="llama-3.1-8b-instant",
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

            res = structured_llm.invoke(prompt)
            return res if isinstance(res, SearchInput) else SearchInput.model_validate(res)
        except Exception as e:
            print(f"[Warning] Groq intent extraction fallback triggered: {e}")

    return SearchInput(semantic_query=user_query)


def _gender_variants(gender: str) -> list[str]:
    if gender == "female":
        return ["female", "unisex", "FEMALE", "UNISEX", "Female", "Unisex"]
    if gender == "male":
        return ["male", "unisex", "MALE", "UNISEX", "Male", "Unisex"]
    return ["unisex", "UNISEX", "Unisex"]


def _case_variants(value: str) -> list[str]:
    return list({value.lower(), value.title(), value.upper()})


def build_pre_filter(intent: SearchInput, tier: int = 1) -> dict[str, Any]:
    conditions: list[dict[str, Any]] = [
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


def hybrid_product_search(intent: SearchInput, limit: int = 5) -> list[dict[str, Any]]:
    """
    Pure Vector Search Engine: Resolved SearchInput leta hai aur MongoDB Atlas se matching products return karta hai.
    """
    db = get_db()
    model = get_model()

    query_parts = [intent.semantic_query]
    if intent.style:
        query_parts.append(f"style: {intent.style}")
    if intent.season:
        query_parts.append(f"season: {intent.season}")
    if intent.vibe_keywords:
        query_parts.append("vibe: " + ", ".join(intent.vibe_keywords))

    query_vector = model.encode(
        " | ".join(query_parts), normalize_embeddings=True
    ).tolist()

    pipeline: list[dict[str, Any]] = [
        {
            "$vectorSearch": {
                "index": settings.vector_index_name,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": int(max(limit * 20, 100)),
                "limit": int(limit),
                "filter": build_pre_filter(intent, tier=1),
            }
        },
        {
            "$project": {
                "_id": 1,
                "name": 1,
                "price": 1,
                "intent": 1,
                "gift_for": 1,
                "occasions": 1,
                "rating": 1,
                "semantic_text": 1,
                "search_text": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    results = list(db["products"].aggregate(pipeline))

    # Tier 2 Fallback: gift_for/occasion hatao, lekin gender + max_price lock rakho
    if not results and (intent.gift_for or intent.occasion):
        pipeline[0]["$vectorSearch"]["filter"] = build_pre_filter(intent, tier=2)
        results = list(db["products"].aggregate(pipeline))

    # Tier 3 Fallback: Sirf budget + stock
    if not results and intent.gender:
        pipeline[0]["$vectorSearch"]["filter"] = build_pre_filter(intent, tier=3)
        results = list(db["products"].aggregate(pipeline))

    return results