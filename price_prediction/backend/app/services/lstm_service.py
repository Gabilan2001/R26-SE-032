"""
LSTM Service (Deprecated legacy wrapper).

Replaced by app.services.decision_engine_service.get_full_recommendation,
which handles per-series models (Dambulla-Retail, Dambulla-Wholesale, Pettah-Retail, Pettah-Wholesale),
calibrated 14-day weather adjustments, and IsolationForest anomaly detection.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from app.schemas.prediction_schema import PricePredictionRequest, PricePredictionResponse
from app.services.decision_engine_service import get_full_recommendation

logger = logging.getLogger(__name__)


def generate_price_prediction(request: PricePredictionRequest) -> PricePredictionResponse:
    """
    Deprecated entry point: delegates to Decision Engine service.
    """
    logger.info("Delegating prediction request to per-series Decision Engine service.")
    market = request.market or "Dambulla"
    series_type = request.type or "Retail"
    target_date_str = (
        request.target_date.strftime("%Y-%m-%d")
        if request.target_date
        else datetime.now().strftime("%Y-%m-%d")
    )
    horizon = request.forecast_horizon_days or 14

    rec_dict = get_full_recommendation(
        market=market,
        series_type=series_type,
        target_date_str=target_date_str,
        horizon_days=horizon,
    )

    return PricePredictionResponse(
        series=rec_dict["series"],
        market=rec_dict["market"],
        type=rec_dict["type"],
        target_date=rec_dict["target_date"],
        current_price_lkr=rec_dict["current_price_lkr"],
        recommendation=rec_dict["recommendation"],
        reasoning=rec_dict["reasoning"],
        base_lstm_forecast=rec_dict["base_lstm_forecast"],
        weather_adjusted_forecast=rec_dict["weather_adjusted_forecast"],
        predicted_prices=[f"{p:.2f}" for p in rec_dict["weather_adjusted_forecast"]],
        predicted_price=rec_dict["day1_forecast_lkr"],
        weather_flag_level=rec_dict["weather_flag_level"],
        d14_cum_rain_mm=rec_dict["d14_cum_rain_mm"],
        is_anomaly=rec_dict["is_anomaly"],
        anomaly_severity=rec_dict["anomaly_severity"],
        anomaly_score=rec_dict["anomaly_score"],
        residual_lkr=rec_dict["residual_lkr"],
        pct_change_day1=rec_dict["pct_change_day1"],
        volatility_threshold_pct=rec_dict["volatility_threshold_pct"],
        driver_share_lstm_pct=rec_dict["driver_share_lstm_pct"],
        driver_share_weather_pct=rec_dict["driver_share_weather_pct"],
        day1_forecast_lkr=rec_dict["day1_forecast_lkr"],
        day14_forecast_lkr=rec_dict["day14_forecast_lkr"],
        currency=request.currency or "LKR/kg",
        forecast_horizon_days=horizon,
    )
