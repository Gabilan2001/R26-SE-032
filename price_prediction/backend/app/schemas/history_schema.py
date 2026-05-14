from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class HistoryRecord(BaseModel):
    """Document stored after each successful prediction (MongoDB)."""

    location: str
    forecast_horizon_days: int
    predicted_prices: list[str]
    currency: str
    recommended_action: str
    weather_signal: str
    news_uncertainty: str
    confidence_score: Optional[float] = Field(None, description="Blended confidence after weather/news.")
    explanation: Optional[str] = Field(None, description="Full narrative saved for audit.")
    news_sentiment: Optional[str] = Field(None, description="Sentiment label at prediction time.")
    # Extended analytics (optional for older clients / records).
    target_date: Optional[str] = Field(None, description="ISO target date if the user requested one.")
    predicted_price_focal: Optional[float] = Field(None, description="Single focal price for reporting.")
    reasons: Optional[list[str]] = Field(None, description="Explainable AI bullet list.")
    farmer_recommendation: Optional[dict[str, Any]] = Field(
        None,
        description="Structured recommendation (action, risk, hints).",
    )
    news_market_analysis: Optional[dict[str, Any]] = Field(
        None,
        description="Filtered news impact payload.",
    )
    weather_summary: Optional[str] = Field(None, description="Primary weather explanation string.")
    created_by: Optional[str] = Field(None, description="Optional user or module identifier")
    timestamp: Optional[datetime] = None


class HistoryResponse(BaseModel):
    success: bool
    record_id: str
