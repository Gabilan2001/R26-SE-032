"""
Weather API Utility
Gets real-time weather data using GPS coordinates
Computes Weather Risk Score for disease spread
"""

import requests
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── API Key ───────────────────────────────────────────
# Put your OpenWeatherMap API key here
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "1395cd70d2f83cc0348b30002b031d4f")
BASE_URL        = "https://api.openweathermap.org/data/2.5/weather"


def get_weather_data(lat: float, lon: float):
    """
    Fetch current weather from OpenWeatherMap API
    
    Returns dict with temperature, humidity, rainfall
    or None if API call fails
    """
    try:
        params = {
            "lat":   lat,
            "lon":   lon,
            "appid": WEATHER_API_KEY,
            "units": "metric"   # Celsius
        }
        response = requests.get(BASE_URL, params=params, timeout=5)
        print(f"[DEBUG] Weather API response status={response.status_code} body={response.text}")
        logger.debug("Weather API response status=%s body=%s", response.status_code, response.text)
        
        if response.status_code == 200:
            data = response.json()

            if not data.get("main") or not data.get("wind") or not data.get("weather"):
                logger.debug("Weather API response missing required fields: %s", data)
                return None
            
            weather = {
                "temperature":    data["main"]["temp"],
                "humidity":       data["main"]["humidity"],
                "rainfall_1h":    data.get("rain", {}).get("1h", 0.0),
                "rainfall_3h":    data.get("rain", {}).get("3h", 0.0),
                "wind_speed":     data["wind"]["speed"],
                "weather_desc":   data["weather"][0]["description"],
                "condition":      data["weather"][0].get("main"),
                "city":           data.get("name", "Unknown"),
                "timestamp":      datetime.now().isoformat()
            }
            print(f"[DEBUG] Extracted weather data: {weather}")
            logger.debug("Extracted weather data: %s", weather)
            return weather
        else:
            print(f"[DEBUG] Weather API error status={response.status_code} body={response.text}")
            logger.debug("Weather API error status=%s body=%s", response.status_code, response.text)
            return None

    except requests.exceptions.Timeout:
        print("[DEBUG] Weather API timeout")
        logger.debug("Weather API timeout")
        return None
    except Exception as e:
        print(f"[DEBUG] Weather API error: {e}")
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

    humidity    = weather["humidity"]
    rainfall    = weather["rainfall_1h"]
    temperature = weather["temperature"]

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
            f"High fungal risk! Humidity {humidity}%, "
            f"Rainfall {rainfall}mm. Treatment may wash away. "
            f"Consider re-spraying after weather improves."
        )
    elif risk_score >= 40:
        risk_level = "MEDIUM"
        alert = (
            f"Moderate risk. Monitor conditions. "
            f"Humidity {humidity}%, Temp {temperature}°C."
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
            "rainfall_1h":     rainfall,
            "temp_deviation":  temp_deviation,
            "wind_speed":      weather["wind_speed"],
            "condition":       weather["condition"],
            "description":     weather["weather_desc"]
        }
    }


def get_weather_risk(lat: float, lon: float) -> dict:
    """
    Main function called by leaf_service.py
    
    Returns complete weather risk assessment
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
    print(f"[DEBUG] Weather risk result: {result}")
    logger.debug("Weather risk result: %s", result)
    return result
