from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.schemas.history_schema import HistoryRecord
from app.schemas.prediction_schema import PricePredictionRequest, PricePredictionResponse
from app.services.decision_engine_service import get_full_recommendation
from app.utils.db_utils import save_history_record

router = APIRouter()

SUPPORTED_MARKETS = {"Dambulla", "Pettah"}
SUPPORTED_TYPES = {"Retail", "Wholesale"}


@router.post("/", response_model=PricePredictionResponse)
def predict_price(request: PricePredictionRequest):
    """Predict future tomato prices using unified Decision Engine (LSTM + Weather + IsolationForest Anomaly Detection)."""
    try:
        market = request.market.strip().capitalize() if request.market else "Dambulla"
        series_type = request.type.strip().capitalize() if request.type else "Retail"

        # Map and sanitize market and series_type
        if market not in SUPPORTED_MARKETS:
            market = "Dambulla"
        if series_type not in SUPPORTED_TYPES:
            series_type = "Retail"

        request_date_str = datetime.now().strftime("%Y-%m-%d")
        target_date_val = request.target_date.strftime("%Y-%m-%d") if request.target_date else None
        target_date_for_engine = target_date_val if target_date_val else request_date_str

        horizon = request.forecast_horizon_days or 14

        rec_dict = get_full_recommendation(
            market=market,
            series_type=series_type,
            target_date_str=target_date_for_engine,
            horizon_days=horizon,
        )

        response_payload = PricePredictionResponse(
            series=rec_dict["series"],
            market=rec_dict["market"],
            type=rec_dict["type"],
            request_date=request_date_str,
            target_date=target_date_val,
            current_price_lkr=rec_dict["current_price_lkr"],
            data_as_of_date=rec_dict.get("data_as_of_date", "2026-03-10"),
            dataset_coverage=rec_dict.get("dataset_coverage", "Aug 2016 to Mar 2026"),
            forecast_dates=rec_dict.get("forecast_dates", []),
            forecast_start_date=rec_dict.get("forecast_start_date", ""),
            forecast_end_date=rec_dict.get("forecast_end_date", ""),
            forecast_period_label=rec_dict.get("forecast_period_label", ""),
            recommendation=rec_dict["recommendation"],
            reasoning=rec_dict["reasoning"],

            base_lstm_forecast=rec_dict["base_lstm_forecast"],
            weather_adjusted_forecast=rec_dict["weather_adjusted_forecast"],
            predicted_prices=[f"{p:.2f}" for p in rec_dict["weather_adjusted_forecast"]],
            predicted_price=rec_dict["day1_forecast_lkr"],
            weather_flag_level=rec_dict["weather_flag_level"],
            d14_cum_rain_mm=rec_dict["d14_cum_rain_mm"],
            regional_weather_impact=rec_dict.get("regional_weather_impact"),
            news_flag_level=rec_dict.get("news_flag_level", "none"),
            news_events=rec_dict.get("news_events", []),
            shap_explanation=rec_dict.get("shap_explanation"),
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

        # Log history to MongoDB if available
        try:
            history_record = HistoryRecord(
                location=rec_dict["series"],
                series=rec_dict["series"],
                market=rec_dict["market"],
                type=rec_dict["type"],
                forecast_horizon_days=horizon,
                predicted_prices=response_payload.predicted_prices,
                currency=response_payload.currency,
                recommended_action=rec_dict["recommendation"],
                recommendation=rec_dict["recommendation"],
                weather_signal=rec_dict["weather_flag_level"],
                weather_flag_level=rec_dict["weather_flag_level"],
                d14_cum_rain_mm=rec_dict["d14_cum_rain_mm"],
                is_anomaly=rec_dict["is_anomaly"],
                anomaly_severity=rec_dict["anomaly_severity"],
                anomaly_score=rec_dict["anomaly_score"],
                residual_lkr=rec_dict["residual_lkr"],
                news_uncertainty="LOW",
                confidence_score=0.90 if not rec_dict["is_anomaly"] else 0.50,
                explanation=rec_dict["reasoning"],
                reasoning=rec_dict["reasoning"],
                current_price_lkr=rec_dict["current_price_lkr"],
                base_lstm_forecast=rec_dict["base_lstm_forecast"],
                weather_adjusted_forecast=rec_dict["weather_adjusted_forecast"],
                target_date=rec_dict["target_date"],
                predicted_price_focal=rec_dict["day1_forecast_lkr"],
            )
            save_history_record(history_record)
        except Exception:
            pass

        return response_payload

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
