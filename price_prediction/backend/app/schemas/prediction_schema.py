from pydantic import BaseModel, Field
from typing import List


class PricePredictionRequest(BaseModel):
    past_prices: List[float] = Field(..., description="Recent observed tomato prices")
    currency: str = Field("USD/kg", description="Currency unit for the forecasted prices")
    forecast_horizon_days: int = Field(7, description="Number of days to forecast")
    window_size: int = Field(14, description="LSTM sequence window size")


class PricePredictionResponse(BaseModel):
    predicted_prices: List[str]
    currency: str
    forecast_horizon_days: int
    recommended_action: str
    confidence_score: float
    weather_signal: str
    news_uncertainty: str
