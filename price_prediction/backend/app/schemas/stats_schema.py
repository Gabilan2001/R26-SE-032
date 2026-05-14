from pydantic import BaseModel


class StatsResponse(BaseModel):
    total_predictions: int
    average_confidence: float
    most_active_location: str
    latest_price_trend: str
    weather_signal_distribution: dict[str, int]
