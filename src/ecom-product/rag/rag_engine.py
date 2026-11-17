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
                model="llama-3.3-70b-versatile",
                temperature=0,
                max_retries=2,
            )
            structured_llm = llm.with_structured_output(SearchInput)
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
        conditions.append({"occasion": {"$in": [intent.occasion.lower()]}})

    return {"$and": conditions} if len(conditions) > 1 else conditions[0]    

   