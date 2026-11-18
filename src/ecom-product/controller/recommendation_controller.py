from fastapi import HTTPException
import time
from ..models.recommendation import ProductItem, RecommendedRequest, RecommendResponse
from ..rag.rag_engine import hybrid_product_search
from ..services.advisor import ai_advisor


def handle_product_recommandations(payload: RecommendedRequest) -> RecommendResponse:
    """Request leta hai, hybrid search + AI advisor chalata hai, aur clean response banata hai."""
    start = time.perf_counter()

    try:
        search_result = hybrid_product_search(
            user_query= payload.query,
            limit = payload.limit
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search pipeline error: {str(e)}")

    raw_products = search_result["products"]

    formatted_products = [
        ProductItem(
            id= str(p["_id"]),
            name=p.get("name", "Unknown Product"),
            brand_name=p.get("brand_name", ""),
            selling_price=p.get("price", {}).get("selling_price"),
            mrp=p.get("price", {}).get("mrp"),
            gift_for=p.get("gift_for", []),
            occasions=p.get("occasions", []),
            score=round(float(p.get("score", 0.0)), 4),
        )

        for p in raw_products
    ]

    ai_summary = (
        ai_advisor(payload.query, raw_products)
        if(payload.include_ai_summary) else None
    )

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    return RecommendResponse(
        query = payload.query,
        extracted_intent=search_result["extracted_intent"],
        ai_recommendation=ai_summary,
        total_data = len(formatted_products),
        latency_ms= elapsed_ms,
        products= formatted_products
    )