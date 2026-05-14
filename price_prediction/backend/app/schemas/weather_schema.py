from pydantic import BaseModel


class WeatherResponse(BaseModel):
    location: str
    weather_signal: str
    expected_temperature_celsius: float
    storm_risk_level: str
    market_impact_score: float
