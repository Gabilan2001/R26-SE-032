"""
Weather API Utility
Gets real-time weather data using GPS coordinates
Computes Weather Risk Score for disease spread
"""

import math
import os
import logging
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── API Key ───────────────────────────────────────────
# Put your OpenWeatherMap API key here
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY") or os.getenv("OPENWEATHER_API_KEY", "")
BASE_URL        = "https://api.openweathermap.org/data/2.5/weather"


def _dew_point_c(temperature_c: float, humidity_pct: float) -> Optional[float]:
    """Magnus approximation. OpenWeather current weather does not return dew point."""
    try:
        t = float(temperature_c)
        rh = min(100.0, max(1.0, float(humidity_pct)))
        a, b = 17.27, 237.7
        gamma = (a * t / (b + t)) + math.log(rh / 100.0)
        return round((b * gamma) / (a - gamma), 1)
    except Exception:
        return None


def _vpd_kpa(temperature_c: float, humidity_pct: float) -> Optional[float]:
    """Vapour-pressure deficit from temperature and relative humidity (kPa)."""
    try:
        t = float(temperature_c)
        rh = min(100.0, max(0.0, float(humidity_pct)))
        es = 0.6108 * math.exp((17.27 * t) / (t + 237.3))
        ea = es * (rh / 100.0)
        return round(max(0.0, es - ea), 2)
    except Exception:
        return None


def get_weather_data(lat: float, lon: float):
    """
    Fetch current weather from OpenWeatherMap API.

    Returns a snapshot dict or None if the API call fails.
    Missing API key / timeout / HTTP errors never raise.
    """
    if not WEATHER_API_KEY:
        logger.debug("Weather API key not configured")
        return None

    try:
        params = {
            "lat":   lat,
            "lon":   lon,
            "appid": WEATHER_API_KEY,
            "units": "metric"   # Celsius
        }
        response = requests.get(BASE_URL, params=params, timeout=5)
        logger.debug("Weather API response status=%s", response.status_code)

        if response.status_code != 200:
            logger.debug("Weather API error status=%s body=%s", response.status_code, response.text)
            return None

        data = response.json()
        main = data.get("main") or {}
        wind = data.get("wind") or {}
        weather_list = data.get("weather") or []
        if not main or not weather_list:
            logger.debug("Weather API response missing required fields: %s", data)
            return None

        temperature = main.get("temp")
        humidity = main.get("humidity")
        wind_ms = float(wind.get("speed") or 0.0)
        gust_ms = wind.get("gust")
        rain_1h = float((data.get("rain") or {}).get("1h") or 0.0)
        rain_3h = float((data.get("rain") or {}).get("3h") or 0.0)
        clouds = (data.get("clouds") or {}).get("all")
        visibility_m = data.get("visibility")

        weather = {
            "temperature":    temperature,
            "humidity":       humidity,
            "rainfall_1h":    rain_1h,
            "rainfall_3h":    rain_3h,
            "wind_speed":     wind_ms,
            "wind_speed_kmh": round(wind_ms * 3.6, 1),
            "wind_gust_kmh":  round(float(gust_ms) * 3.6, 1) if gust_ms is not None else None,
            "cloud_cover":    clouds,
            "visibility_km":  round(float(visibility_m) / 1000.0, 1) if visibility_m else None,
            "dew_point":      _dew_point_c(temperature, humidity) if temperature is not None and humidity is not None else None,
            "vpd_kpa":        _vpd_kpa(temperature, humidity) if temperature is not None and humidity is not None else None,
            "weather_desc":   weather_list[0].get("description"),
            "condition":      weather_list[0].get("main"),
            "city":           data.get("name", "Unknown"),
            "timestamp":      datetime.now().isoformat(),
        }
        logger.debug("Extracted weather data: %s", weather)
        return weather

    except requests.exceptions.Timeout:
        logger.debug("Weather API timeout")
        return None
    except Exception as e:
        logger.debug("Weather API error: %s", e)
        return None


def compute_weather_risk_score(weather: dict) -> dict:
    """
    Compute Weather Risk Score using your proposal formula:
    Risk = (Humidity × 0.4) + (Rainfall × 0.4) + (Temp_deviation × 0.2)
    
    Higher score = higher risk of disease spread
    """
    if weather is None:
        return {
            "risk_score":  0.0,
            "risk_level":  "UNKNOWN",
            "alert":       None,
            "details":     {}
        }

    humidity    = weather.get("humidity")
    rainfall    = weather.get("rainfall_1h") or 0.0
    temperature = weather.get("temperature")
    if humidity is None or temperature is None:
        return {
            "risk_score":  0.0,
            "risk_level":  "UNKNOWN",
            "alert":       None,
            "details":     {}
        }

    humidity = float(humidity)
    rainfall = float(rainfall)
    temperature = float(temperature)

    # Temperature deviation from ideal (25°C is ideal for tomatoes)
    temp_deviation = abs(temperature - 25)

    # Your formula from proposal
    risk_score = (
        (humidity       * 0.4) +
        (rainfall * 10  * 0.4) +  # scale rainfall to 0-100
        (temp_deviation * 0.2)
    )

    # Clamp to 0-100
    risk_score = min(100, max(0, round(risk_score, 2)))

    # Risk level classification
    if risk_score >= 70:
        risk_level = "HIGH"
        alert = (
            f"High weather-related disease pressure. Humidity {humidity}%, "
            f"Rainfall {rainfall}mm. Conditions may favour continued disease "
            f"development — increase observation frequency."
        )
    elif risk_score >= 40:
        risk_level = "MEDIUM"
        alert = (
            f"Moderate weather-related disease pressure. "
            f"Humidity {humidity}%, Temp {temperature}°C. Continue monitoring."
        )
    else:
        risk_level = "LOW"
        alert = None

    return {
        "risk_score":      risk_score,
        "risk_level":      risk_level,
        "alert":           alert,
        "details": {
            "humidity":        humidity,
            "temperature":     temperature,
            "rainfall":        rainfall,
            "rainfall_1h":     rainfall,
            "rainfall_3h":     weather.get("rainfall_3h", 0.0),
            "temp_deviation":  temp_deviation,
            "wind_speed":      weather.get("wind_speed"),
            "wind_speed_kmh":  weather.get("wind_speed_kmh"),
            "wind_gust_kmh":   weather.get("wind_gust_kmh"),
            "cloud_cover":     weather.get("cloud_cover"),
            "dew_point":       weather.get("dew_point"),
            "visibility_km":   weather.get("visibility_km"),
            "vpd_kpa":         weather.get("vpd_kpa"),
            "condition":       weather.get("condition"),
            "description":     weather.get("weather_desc"),
        }
    }


def get_weather_risk(lat: float, lon: float) -> dict:
    """
    Fetch weather and compute contextual risk for observation records.
    """
    weather = get_weather_data(lat, lon)

    if weather is None:
        # Fallback if API fails
        return {
            "risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "alert":      "Weather data unavailable",
            "details":    {}
        }

    risk = compute_weather_risk_score(weather)

    result = {
        "risk_score":  risk["risk_score"],
        "risk_level":  risk["risk_level"],
        "alert":       risk["alert"],
        "details":     risk["details"],
        "city":        weather["city"],
        "timestamp":   weather["timestamp"]
    }
    logger.debug("Weather risk result: %s", result)
    return result
