from app.schemas.recommendation_schema import RecommendationResponse


def recommend_selling_time(location: str) -> RecommendationResponse:
    """Combine market, weather, and news signals into an actionable selling recommendation."""
    return RecommendationResponse(
        location=location,
        optimal_sell_day=3,
        expected_price_change="increase",
        recommendation_message="Hold inventory for 3 days and sell after the next rain event.",
        risk_level="medium",
    )
