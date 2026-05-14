from fastapi import APIRouter, HTTPException

from app.schemas.weather_schema import WeatherRequest, WeatherResponse
from app.services.weather_service import fetch_weather_signal

router = APIRouter()


@router.get("/", response_model=WeatherResponse)
def weather_insight(location: str):
    """Return weather-driven market signals for a given farm location."""
    try:
        return fetch_weather_signal(location)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
