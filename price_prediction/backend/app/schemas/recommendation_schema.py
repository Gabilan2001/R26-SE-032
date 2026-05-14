from typing import List, Optional

from pydantic import BaseModel, Field


class RecommendationResponse(BaseModel):
    """Selling guidance (quick route — full detail on POST /predict/)."""

    location: str
    optimal_sell_day: int
    expected_price_change: str
    recommendation_message: str
    risk_level: str
    action: Optional[str] = Field(None, description="SELL_NOW or WAIT when derived from live signals.")
    confidence_score: Optional[float] = None
    market_risk: Optional[str] = Field(None, description="LOW | MEDIUM | HIGH")
    reasons: List[str] = Field(default_factory=list, description="Short bullets from weather + news.")
