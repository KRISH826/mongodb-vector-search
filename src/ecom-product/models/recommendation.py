from typing import Any
from pydantic import BaseModel, Field

from typing import Any
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=300,
        examples=["meri wife ke liye birthday gift suggest kar 5000 tak"],
    )
    limit: int = Field(default=5, ge=1, le=50)
    include_ai_summary: bool = Field(default=True)

class ProductItem(BaseModel):
    id: str
    name: str
    selling_price: float | int | None = None
    mrp: float | int | None = None
    gender: str | None = None
    style: str | None = None
    vibe_keywords: list[str] = Field(default_factory=list)
    gift_for: list[str] = Field(default_factory=list)
    occasions: list[str] = Field(default_factory=list)
    rating: float | None = None
    score: float

class RecommendResponse(BaseModel):
    query: str
    extracted_intent: dict[str, Any]
    ai_recommendation: str | None = None
    total_found: int
    latency_ms: float
    products: list[ProductItem]