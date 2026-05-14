from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    location: str
    optimal_sell_day: int
    expected_price_change: str
    recommendation_message: str
    risk_level: str
