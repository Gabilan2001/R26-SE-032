import logging
from datetime import datetime
from typing import List

import numpy as np
from zoneinfo import ZoneInfo

from app.models.lstm_model import load_price_model, load_scaler
from app.schemas.history_schema import HistoryRecord
from app.schemas.prediction_schema import (
    FarmerRecommendation,
    PricePredictionRequest,
    PricePredictionResponse,
    compute_horizon_for_target,
)
from app.services.explanation_service import build_explanation_reasons
from app.services.news_impact_service import analyze_agriculture_news_for_location
from app.services.preprocessing_service import prepare_time_series_features
from app.services.recommendation_engine import build_farmer_recommendation
from app.services.weather_service import fetch_weather_signal
from app.utils.db_utils import save_history_record

logger = logging.getLogger(__name__)
TZ_COLOMBO = ZoneInfo("Asia/Colombo")


def _currency_label(currency: str) -> str:
    """Turn 'LKR/kg' into 'LKR' for short sentences."""
    if "/" in currency:
        return currency.split("/")[0].strip()
    return currency.strip()


def _blend_confidence(weather_impact: str, news_sentiment: str) -> float:
    """Blend model confidence from weather impact + news sentiment labels."""
    base = 0.80
    if weather_impact == "HIGH":
        base -= 0.10
    elif weather_impact == "MEDIUM":
        base -= 0.05

    if news_sentiment == "very_negative":
        base -= 0.10
    elif news_sentiment == "negative":
        base -= 0.05
    elif news_sentiment == "positive":
        base += 0.05

    return max(0.30, min(0.99, round(base, 3)))


def generate_price_prediction(request: PricePredictionRequest) -> PricePredictionResponse:
    """
    Full agricultural decision path:

      * Location drives Open-Meteo coordinates and news query context.
      * News is fetched and filtered automatically (no manual news query).
      * Optional target_date extends horizon (capped) and picks a focal price day.
      * Rule-based reasons + selling recommendation are attached for explainability.
    """
    location = (request.location or "Dambulla").strip()

    model = load_price_model()
    scaler = load_scaler()

    expected_window = int(model.input_shape[1])
    if request.window_size != expected_window:
        logger.info(
            "window_size %s != model %s; using model window.",
            request.window_size,
            expected_window,
        )
    if len(request.past_prices) < expected_window:
        raise ValueError(
            f"Need at least {expected_window} past prices for this model; got {len(request.past_prices)}."
        )

    horizon, target_note, target_resolved = compute_horizon_for_target(
        request.target_date,
        request.forecast_horizon_days,
    )

    weather = fetch_weather_signal(location, forecast_days=horizon)
    news = analyze_agriculture_news_for_location(location)

    raw_prices = np.array(request.past_prices).reshape(-1, 1)
    scaled_prices = scaler.transform(raw_prices).flatten().tolist()
    current_window = prepare_time_series_features(scaled_prices, expected_window)

    forecast_scaled: List[float] = []
    for _ in range(horizon):
        pred_scaled = model.predict(current_window, verbose=0)
        forecast_scaled.append(float(pred_scaled[0, 0]))
        current_window = np.append(current_window[:, 1:, :], [[[pred_scaled[0, 0]]]], axis=1)

    forecast_raw = scaler.inverse_transform(np.array(forecast_scaled).reshape(-1, 1)).flatten().tolist()

    last_price = float(request.past_prices[-1])
    mean_forecast = float(np.mean(forecast_raw))
    best_idx = int(np.argmax(forecast_raw))
    best_price = float(forecast_raw[best_idx])
    unit = _currency_label(request.currency)

    # Focal price: calendar day if requested, otherwise horizon average (stable headline number).
    focal_idx = best_idx
    focal_price: float
    target_iso: str | None = None
    if request.target_date and target_resolved:
        today = datetime.now(TZ_COLOMBO).date()
        days_ahead = (target_resolved - today).days
        if days_ahead == 0:
            days_ahead = 1
        focal_idx = min(max(days_ahead - 1, 0), len(forecast_raw) - 1)
        target_iso = target_resolved.isoformat()
        focal_price = float(forecast_raw[focal_idx])
    else:
        focal_price = float(mean_forecast)

    confidence = _blend_confidence(weather.impact, news.news_sentiment)

    action, timing_hint, move_hint, risk, rec_msg = build_farmer_recommendation(
        weather,
        news,
        last_price,
        best_idx,
        best_price,
        mean_forecast,
        focal_price,
        unit,
    )

    farmer_rec = FarmerRecommendation(
        action=action,
        confidence_score=confidence,
        market_risk=risk,
        sell_timing_hint=timing_hint,
        expected_price_change_hint=move_hint,
    )

    reasons = build_explanation_reasons(
        location,
        weather,
        news,
        last_price,
        focal_price,
        mean_forecast,
        best_idx,
        best_price,
        unit,
    )

    explanation = (
        f"Predicted focal price near {unit} {focal_price:.0f} for {location}. "
        f"{farmer_rec.sell_timing_hint} "
        f"Weather: {weather.weather_signal}. News impact: {news.price_impact_direction}. "
        f"Confidence {confidence:.2f}."
    )

    recommended_action = (
        f"Best time to sell: Day {best_idx + 1} at {best_price:.2f} {unit}. {action}: {timing_hint}"
    )

    data_sources = {
        "weather": weather.data_source,
        "news": news.data_source,
        "model": "Bidirectional LSTM v1",
    }

    response = PricePredictionResponse(
        predicted_prices=[f"{value:.2f}" for value in forecast_raw],
        predicted_price=round(focal_price, 2),
        target_date=target_iso,
        target_date_note=target_note,
        currency=request.currency,
        forecast_horizon_days=horizon,
        location=location,
        reasons=reasons,
        farmer_recommendation=farmer_rec,
        news_market_analysis=news,
        recommended_action=recommended_action,
        confidence_score=confidence,
        weather_signal=weather.weather_signal,
        news_uncertainty=news.uncertainty_level,
        explanation=explanation,
        weather_market_impact_score=weather.market_impact_score,
        weather_reason=weather.reason,
        news_sentiment=news.news_sentiment,
        news_headlines=news.relevant_headlines[:3],
        data_sources=data_sources,
    )

    # Richer MongoDB document for audits.
    try:
        record = HistoryRecord(
            location=location,
            forecast_horizon_days=horizon,
            predicted_prices=response.predicted_prices,
            currency=request.currency,
            recommended_action=recommended_action,
            weather_signal=weather.weather_signal,
            news_uncertainty=news.uncertainty_level,
            confidence_score=confidence,
            explanation=explanation,
            news_sentiment=news.news_sentiment,
            target_date=target_iso,
            predicted_price_focal=focal_price,
            reasons=reasons,
            farmer_recommendation=farmer_rec.model_dump(),
            news_market_analysis=news.model_dump(),
            weather_summary=weather.reason,
        )
        save_history_record(record)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Prediction history not saved: %s", exc)

    return response
