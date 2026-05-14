from app.schemas.recommendation_schema import RecommendationResponse
from app.services.news_impact_service import analyze_agriculture_news_for_location
from app.services.recommendation_engine import build_farmer_recommendation
from app.services.weather_service import fetch_weather_signal


def recommend_selling_time(location: str) -> RecommendationResponse:
    """
    Lightweight recommendation using live weather + automated news (no LSTM).

    For a full price trajectory use POST /predict/.
    """
    loc = (location or "Dambulla").strip()
    weather = fetch_weather_signal(loc, forecast_days=7)
    news = analyze_agriculture_news_for_location(loc)
    confidence = 0.75
    action, timing, move, risk, msg = build_farmer_recommendation(
        weather,
        news,
        last_price=100.0,
        best_day_index=2,
        best_price=105.0,
        mean_forecast=102.0,
        focal_price=102.0,
        currency_unit="LKR",
    )
    # Heuristic optimal day when WAIT else 1
    optimal = 3 if action == "WAIT" else 1
    return RecommendationResponse(
        location=loc,
        optimal_sell_day=optimal,
        expected_price_change=move,
        recommendation_message=msg,
        risk_level=risk.lower(),
        action=action,
        confidence_score=confidence,
        market_risk=risk,
        reasons=[weather.reason, news.market_impact_summary],
    )
