from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class HistoryRecord(BaseModel):
    location: str
    forecast_horizon_days: int
    predicted_prices: list[str]
    currency: str
    recommended_action: str
    weather_signal: str
    news_uncertainty: str
    created_by: Optional[str] = Field(None, description="Optional user or module identifier")
    timestamp: Optional[datetime] = None


class HistoryResponse(BaseModel):
    success: bool
    record_id: str
