from app.schemas.prediction_schema import PricePredictionRequest
from app.services.lstm_service import generate_price_prediction


def test():
    # Omit past_prices — service loads the last window from datasets/ (same logic as training).
    req = PricePredictionRequest(
        window_size=10,
        forecast_horizon_days=3,
        currency="LKR/kg",
        location="Dambulla",
    )
    res = generate_price_prediction(req)
    print("past_prices_source:", res.past_prices_source)
    print("past_prices_used:", res.past_prices_used)
    print("Prediction Response:")
    print(res.model_dump_json(indent=2))


if __name__ == "__main__":
    test()
