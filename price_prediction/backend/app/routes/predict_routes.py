from fastapi import APIRouter, HTTPException

from app.schemas.prediction_schema import PricePredictionRequest, PricePredictionResponse
from app.services.lstm_service import generate_price_prediction

router = APIRouter()


@router.post("/", response_model=PricePredictionResponse)
def predict_price(request: PricePredictionRequest):
    """Predict future tomato prices using an LSTM time-series model."""
    try:
        result = generate_price_prediction(request)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
