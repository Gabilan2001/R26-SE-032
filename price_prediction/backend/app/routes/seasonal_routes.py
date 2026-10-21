from fastapi import APIRouter, HTTPException, Query
from app.services.seasonal_service import get_seasonal_planning_forecast

router = APIRouter()

SUPPORTED_MARKETS = {"Dambulla", "Pettah"}
SUPPORTED_TYPES = {"Retail", "Wholesale"}


@router.get("/")
def seasonal_forecast(
    market: str = Query("Dambulla", description="Market location (Dambulla/Pettah)"),
    type: str = Query("Wholesale", description="Series type (Retail/Wholesale)"),
    target_month: int = Query(12, ge=1, le=12, description="Target calendar month (1-12)"),
    target_year: int = Query(2026, ge=2026, le=2030, description="Target calendar year"),
):
    """
    Seasonal Planning Forecast Endpoint.
    Calculates historical price percentiles, trend-adjusted ranges,
    backtest-validated confidence ratings, and composite weather outlooks for long-term target dates.
    """
    try:
        mkt = market.strip().capitalize() if market else "Dambulla"
        tp = type.strip().capitalize() if type else "Wholesale"
        if mkt not in SUPPORTED_MARKETS:
            mkt = "Dambulla"
        if tp not in SUPPORTED_TYPES:
            tp = "Wholesale"

        return get_seasonal_planning_forecast(
            market=mkt,
            series_type=tp,
            target_month=target_month,
            target_year=target_year,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
