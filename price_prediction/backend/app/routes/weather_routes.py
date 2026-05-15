from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.schemas.prediction_schema import compute_horizon_for_target
from app.schemas.weather_schema import WeatherResponse
from app.services.weather_service import fetch_weather_signal

router = APIRouter()


@router.get("/", response_model=WeatherResponse)
def weather_insight(location: str, target_date: Optional[date] = None):
    """
    Return weather-driven market signals for a given farm location.

    When ``target_date`` is set, the Open-Meteo window matches the same horizon
    used for price prediction (today → target, Asia/Colombo calendar, capped).
    Otherwise a 7-day window is used.
    """
    try:
        if target_date is not None:
            horizon, _, _ = compute_horizon_for_target(target_date, 7)
        else:
            horizon = 7
        return fetch_weather_signal(location, forecast_days=horizon)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
