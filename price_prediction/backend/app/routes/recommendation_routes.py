from fastapi import APIRouter, HTTPException

from app.schemas.recommendation_schema import RecommendationResponse
from app.services.recommendation_service import recommend_selling_time

router = APIRouter()


@router.get("/", response_model=RecommendationResponse)
def recommendation(location: str):
    """Return an optimal selling time recommendation for farmers."""
    try:
        return recommend_selling_time(location)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
