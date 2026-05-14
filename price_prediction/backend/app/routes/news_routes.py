from fastapi import APIRouter, HTTPException

from app.schemas.market_news_schema import NewsMarketAnalysis
from app.schemas.news_schema import NewsResponse
from app.services.news_impact_service import analyze_agriculture_news_for_location
from app.services.news_service import analyze_market_news

router = APIRouter()


@router.get("/", response_model=NewsResponse)
def news_insight(query: str):
    """Return news-based uncertainty analysis for a manual query (developer / debug)."""
    try:
        return analyze_market_news(query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/market-analysis", response_model=NewsMarketAnalysis)
def news_market_analysis(location: str = "Dambulla"):
    """
    Automated agriculture news for the selected location.

    Farmers do not type a news query — the backend fetches and filters articles.
    """
    try:
        return analyze_agriculture_news_for_location(location)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
