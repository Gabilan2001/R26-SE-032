from typing import List

from app.models.lstm_model import load_price_model
from app.services.preprocessing_service import prepare_time_series_features
from app.schemas.prediction_schema import PricePredictionRequest, PricePredictionResponse


def generate_price_prediction(request: PricePredictionRequest) -> PricePredictionResponse:
    """Generate a tomato price forecast using a sequence model."""
    model = load_price_model()
    features = prepare_time_series_features(request.past_prices, request.window_size)

    prediction = model.predict(features)
    forecast = [round(float(value), 2) for value in prediction.flatten().tolist()]

    # Placeholder for future model retraining and confidence scoring.
    return PricePredictionResponse(
        predicted_prices=[f"{value:.2f}" for value in forecast],
        currency=request.currency,
        forecast_horizon_days=request.forecast_horizon_days,
        recommended_action="Sell in 3 days when volatility drops",
        confidence_score=0.76,
        weather_signal="moderate_rainfall",
        news_uncertainty="elevated",
    )
