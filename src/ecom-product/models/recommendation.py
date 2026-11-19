from typing import Any
from pydantic import BaseModel, Field

class RecommendedRequest(BaseModel):
    query: str = Field(
        ...,
        min_length= 2,
        max_length= 300,
        examples=["bhai gaming ke liye ek tagda phone suggest kar 30000 tak"],
    )

    limit: int = Field(default= 5 , ge = 1, le = 20)
    include_ai_summary: bool = Field(default= True)


class ProductItem(BaseModel):
    id: str
    name: str
    brand_name: str
    selling_price: float | int | None = None
    mrp: float | int | None = None
    gift_for: list[str] = []
    occasions: list[str] = []
    score: float


class RecommendResponse(BaseModel):
    query: str
    extracted_intent: dict[str, Any]
    ai_recommendation: str | None = None
    total_data: int
    latency_ms: float
    products: list[ProductItem]
