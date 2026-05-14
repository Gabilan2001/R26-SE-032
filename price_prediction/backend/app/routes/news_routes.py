from fastapi import APIRouter, HTTPException

from app.schemas.news_schema import NewsResponse
from app.services.news_service import analyze_market_news

router = APIRouter()


@router.get("/", response_model=NewsResponse)
def news_insight(query: str):
    """Return news-based uncertainty analysis for a market query."""
    try:
        return analyze_market_news(query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
