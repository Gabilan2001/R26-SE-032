from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class HistoryRecord(BaseModel):
    """Document stored after each successful prediction (MongoDB)."""

    location: str
    series: Optional[str] = None
    market: Optional[str] = None
    type: Optional[str] = None
    forecast_horizon_days: int = 14
    predicted_prices: List[str]
    currency: str = "LKR/kg"
    recommended_action: str
    recommendation: Optional[str] = None
    weather_signal: str
    news_uncertainty: str = "LOW"
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    explanation: Optional[str] = Field(None, description="Narrative string saved for audit")
    reasoning: Optional[str] = Field(None, description="Plain-language reasoning string")
    
    current_price_lkr: Optional[float] = None
    base_lstm_forecast: Optional[List[float]] = None
    weather_adjusted_forecast: Optional[List[float]] = None
    weather_flag_level: Optional[str] = None
    d14_cum_rain_mm: Optional[float] = None
    news_flag_level: Optional[str] = None
    news_events: Optional[List[Any]] = None
    is_anomaly: Optional[bool] = None

    anomaly_severity: Optional[str] = None
    anomaly_score: Optional[float] = None
    residual_lkr: Optional[float] = None

    target_date: Optional[str] = Field(None, description="ISO target date")
    predicted_price_focal: Optional[float] = Field(None, description="Single focal price for reporting")
    created_by: Optional[str] = Field(None, description="Optional user or module identifier")
    timestamp: Optional[datetime] = None


class HistoryResponse(BaseModel):
    success: bool
    record_id: str
