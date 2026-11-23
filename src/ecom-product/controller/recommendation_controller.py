from fastapi import HTTPException
import time
from ..models.recommendation import ProductItem, RecommendResponse, RecommendRequest
from ..rag.checkpointer import resolve_stateful_intent
from ..rag.rag_engine import extract_intent, hybrid_product_search
from ..services.advisor import ai_advisor


def handle_product_recommandations(payload: RecommendRequest) -> RecommendResponse:
    """Request leta hai, hybrid search + AI advisor chalata hai, aur clean response banata hai."""
    start = time.perf_counter()

    try:

        intent = (
            resolve_stateful_intent(payload.query, payload.thread_id)
            if payload.thread_id
            else extract_intent(payload.query)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search pipeline error: {str(e)}")

    raw_products = hybrid_product_search(intent, limit = payload.limit)

    formatted_products = [
        ProductItem(
            id=str(p["_id"]),
            name=p.get("name", "Unknown Product"),
            selling_price=(p.get("price") or {}).get("selling_price"),
            mrp=(p.get("price") or {}).get("mrp"),
            gender=(p.get("intent") or {}).get("gender"),
            style=(p.get("intent") or {}).get("style"),
            vibe_keywords=(p.get("intent") or {}).get("vibe_keywords", []),
            gift_for=p.get("gift_for", []),
            occasions=p.get("occasions", []),
            rating=(p.get("rating") or {}).get("average"),
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
        extracted_intent=dict(intent),
        ai_recommendation=ai_summary,
        total_found = len(formatted_products),
        latency_ms= elapsed_ms,
        products= formatted_products
    )