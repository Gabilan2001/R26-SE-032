"""
Selling recommendation engine — combines LSTM path, weather impact, and news risk.

Outputs discrete actions suitable for a farmer decision-support UI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Tuple

if TYPE_CHECKING:
    from app.schemas.market_news_schema import NewsMarketAnalysis
    from app.schemas.weather_schema import WeatherResponse


def _market_risk(weather_impact: str, news_uncertainty: str) -> Literal["LOW", "MEDIUM", "HIGH"]:
    score = 0
    if weather_impact in ("HIGH", "UNKNOWN"):
        score += 2
    elif weather_impact == "MEDIUM":
        score += 1
    nu = (news_uncertainty or "moderate").lower()
    if nu in ("very_high", "elevated"):
        score += 2
    elif nu == "moderate":
        score += 1
    if score >= 3:
        return "HIGH"
    if score >= 1:
        return "MEDIUM"
    return "LOW"


def build_farmer_recommendation(
    weather: "WeatherResponse",
    news: "NewsMarketAnalysis",
    last_price: float,
    best_day_index: int,
    best_price: float,
    mean_forecast: float,
    focal_price: float,
    currency_unit: str,
) -> Tuple[str, str, str, str, str]:
    """
    Return: action (SELL_NOW|WAIT), sell_timing_hint, expected_move, risk, message.

    Uses the model's best day plus weather/news risk — simple, explainable rules.
    """
    risk = _market_risk(weather.impact, news.uncertainty_level)

    trend_up = focal_price >= last_price * 1.01
    trend_down = focal_price <= last_price * 0.99

    # Best day is 0-indexed; day 0 = first day in the forecast horizon.
    if best_day_index == 0:
        action = "SELL_NOW"
        hint = "SELL NOW — the strongest modelled price is in the first days of your horizon."
        move = (
            f"Model peaks early near {currency_unit} {best_price:.0f} "
            f"(last observed {currency_unit} {last_price:.0f})."
        )
    elif trend_down:
        action = "SELL_NOW"
        hint = "SELL NOW — the trend points down versus your last prices; waiting may reduce margin."
        move = f"Modelled focal price ~{currency_unit} {focal_price:.0f} vs last {last_price:.0f}."
    elif trend_up and best_day_index >= 1:
        action = "WAIT"
        hint = f"WAIT — consider selling after day {best_day_index} (~{currency_unit} {best_price:.0f})."
        move = f"Average modelled level ~{currency_unit} {mean_forecast:.0f} (above recent {last_price:.0f})."
    else:
        action = "WAIT"
        hint = "WAIT — no clear early peak; monitor daily offers before fixing a selling day."
        move = f"Typical modelled level ~{currency_unit} {mean_forecast:.0f}."

    if risk == "HIGH" and action == "WAIT":
        hint += " High weather/news risk — keep a shorter waiting plan."

    msg = f"{action}: {hint} ({move})"
    return action, hint, move, risk, msg
