"""Request/response models for the prediction API (LSTM + explainability)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator
from zoneinfo import ZoneInfo

from app.schemas.market_news_schema import NewsMarketAnalysis

TZ_COLOMBO = ZoneInfo("Asia/Colombo")


class FarmerRecommendation(BaseModel):
    """Structured selling advice returned with each prediction."""

    action: str = Field(..., description="SELL_NOW or WAIT")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    market_risk: str = Field(..., description="LOW | MEDIUM | HIGH")
    sell_timing_hint: str = Field(..., description="Short caps instruction, e.g. SELL AFTER 5 DAYS")
    expected_price_change_hint: str = Field(
        ...,
        description="Plain-language expectation vs recent prices.",
    )


class PricePredictionRequest(BaseModel):
    """Input for price forecast + explainability."""

    location: str = Field(
        "Dambulla",
        description="Market / region (dropdown or free text), e.g. Colombo, Dambulla, Kandy.",
    )
    past_prices: List[float] = Field(..., description="Recent observed tomato prices (same units as training).")
    currency: str = Field("LKR/kg", description="Currency label for responses")
    forecast_horizon_days: int = Field(7, ge=1, le=30, description="Ignored when target_date is set.")
    window_size: int = Field(
        10,
        ge=5,
        le=60,
        description="LSTM look-back; must match saved model input length.",
    )
    target_date: Optional[date] = Field(
        None,
        description="If set, the service forecasts up to this date (Asia/Colombo calendar), max 16 days ahead.",
    )
    market: Optional[str] = Field(
        None,
        description="Deprecated: use `location`. If only `market` is sent, it is copied to `location`.",
    )

    @model_validator(mode="before")
    @classmethod
    def _legacy_market_field(cls, data: Any) -> Any:
        if isinstance(data, dict):
            loc = data.get("location")
            mkt = data.get("market")
            if (loc is None or str(loc).strip() == "") and mkt:
                data = {**data, "location": mkt}
        return data


class PricePredictionResponse(BaseModel):
    """Full prediction + XAI + recommendation payload."""

    predicted_prices: List[str]
    predicted_price: Optional[float] = Field(
        None,
        description="Single focal price: target date if set, else horizon average.",
    )
    target_date: Optional[str] = Field(None, description="Echo ISO date when a target was requested.")
    target_date_note: Optional[str] = Field(
        None,
        description="Set when the requested date is beyond the forecast cap.",
    )
    currency: str
    forecast_horizon_days: int
    location: str = Field("", description="Echo of user location / market label.")
    reasons: List[str] = Field(default_factory=list, description="Explainable AI bullet reasons.")
    farmer_recommendation: FarmerRecommendation
    news_market_analysis: NewsMarketAnalysis
    recommended_action: str
    confidence_score: float
    weather_signal: str
    news_uncertainty: str
    explanation: str = Field("", description="Single paragraph summary.")
    weather_market_impact_score: float = 0.0
    weather_reason: str = ""
    news_sentiment: str = ""
    news_headlines: List[str] = Field(default_factory=list)
    data_sources: Dict[str, str] = Field(default_factory=dict)


def compute_horizon_for_target(target: Optional[date], default_horizon: int) -> tuple[int, Optional[str], Optional[date]]:
    """
    Map optional target_date to LSTM iteration count (capped for weather/news alignment).

    Returns: (horizon_days, note_if_truncated, resolved_target_date)
    """
    if target is None:
        return default_horizon, None, None

    today = datetime.now(TZ_COLOMBO).date()
    days_ahead = (target - today).days
    if days_ahead < 0:
        raise ValueError("target_date cannot be in the past (Asia/Colombo calendar).")
    if days_ahead == 0:
        days_ahead = 1

    max_days = 16
    note = None
    if days_ahead > max_days:
        note = (
            f"target_date is {days_ahead} days ahead; forecast and weather are capped at {max_days} days. "
            f"Price shown uses the last day in that window."
        )
        days_ahead = max_days

    return days_ahead, note, target
