"""Explainable AI: farmer-readable bullet reasons built from model + context."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from app.schemas.market_news_schema import NewsMarketAnalysis
    from app.schemas.weather_schema import WeatherResponse


def build_explanation_reasons(
    location: str,
    weather: "WeatherResponse",
    news: "NewsMarketAnalysis",
    last_price: float,
    focal_price: float,
    mean_forecast: float,
    best_day_index: int,
    best_price: float,
    currency_unit: str,
) -> List[str]:
    """
    Produce ordered, plain-English reasons (rule-based XAI).

    Earlier items are higher priority (weather and safety first).
    """
    reasons: List[str] = []
    loc = location.strip() or "your area"

    # Weather block
    if weather.data_source == "Open-Meteo API":
        if weather.daily_rainfall:
            peak = max(weather.daily_rainfall)
            rain_bits = f"Peak daily rain in the forecast window is up to {peak:.1f} mm"
        else:
            rain_bits = "Rainfall readings are not available for this window"
        temp_bit = f"Typical temperatures are around {weather.expected_temperature_celsius:.1f} °C."
        hum_bit = ""
        if weather.humidity_avg_pct:
            hum_bit = f" Average humidity is about {weather.humidity_avg_pct:.0f}%."
        reasons.append(
            f"Weather near {loc}: {weather.weather_signal.replace('_', ' ')}. "
            f"{rain_bits}. {temp_bit}{hum_bit}"
        )
        reasons.append(weather.reason)
    else:
        reasons.append("Weather data was unavailable; forecast leans on price history and news only.")

    # News / market block
    if news.articles_analyzed > 0:
        topics = ", ".join(news.matched_topics[:6]) if news.matched_topics else "general market news"
        reasons.append(
            f"Recent news ({news.articles_analyzed} articles) points to {news.price_impact_direction} "
            f"price pressure. Themes seen: {topics}."
        )
        reasons.append(news.market_impact_summary)
    else:
        reasons.append(
            "No strong agriculture headlines were matched recently; news is treated as neutral for risk."
        )

    # Price trend from LSTM
    if focal_price > last_price * 1.02:
        reasons.append(
            f"The model expects prices around {currency_unit} {focal_price:.0f}, higher than your last "
            f"observed {last_price:.0f} — demand or tight supply may dominate in the window you picked."
        )
    elif focal_price < last_price * 0.98:
        reasons.append(
            f"The model expects softer prices near {currency_unit} {focal_price:.0f} versus your last "
            f"{last_price:.0f}, which can happen when supply improves or buying slows."
        )
    else:
        reasons.append(
            f"The model sees prices staying close to your recent level (~{currency_unit} {mean_forecast:.0f} "
            "average over the forecast horizon)."
        )

    reasons.append(
        f"Across the simulated days, the strongest modelled price is about {currency_unit} {best_price:.0f} "
        f"on day {best_day_index + 1} of the horizon."
    )

    return reasons
