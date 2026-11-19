from fastapi import APIRouter
from ..controller.recommendation_controller import handle_product_recommandations
from ..models.recommendation import RecommendResponse, RecommendedRequest

router = APIRouter()

@router.get("/health")
def health_check() -> dict[str,str]:
    return {
        "status": "HEALTHY"
    }


@router.post("/recommended", response_model= RecommendResponse)
def ai_recommended_product(payload: RecommendedRequest) -> RecommendResponse:
    return handle_product_recommandations(payload)    