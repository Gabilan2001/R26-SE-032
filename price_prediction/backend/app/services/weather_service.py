from app.schemas.weather_schema import WeatherResponse


def fetch_weather_signal(location: str) -> WeatherResponse:
    """Fetch weather forecasts, transform features, and return a market signal."""
    # Placeholder for API integration and weather feature engineering.
    weather_signal = "rain_expected"
    weather_score = 0.64

    return WeatherResponse(
        location=location,
        weather_signal=weather_signal,
        expected_temperature_celsius=24.5,
        storm_risk_level="moderate",
        market_impact_score=weather_score,
    )
