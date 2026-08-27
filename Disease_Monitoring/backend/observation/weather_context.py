"""Contextual weather interpretation for observations."""

from typing import Any, Dict, Optional

from utils.weather_utils import get_weather_risk


def fetch_weather_context(lat: Optional[float], lon: Optional[float]) -> Optional[Dict[str, Any]]:
    """Fetch weather context when coordinates are provided; returns None on failure."""
    if lat is None or lon is None:
        return None

    try:
        risk = get_weather_risk(lat, lon)
    except Exception:
        return None

    if not risk or risk.get("risk_level") == "UNKNOWN":
        return {
            "available": False,
            "interpretation": "Weather data unavailable for contextual monitoring.",
            "raw": risk,
        }

    humidity = risk.get("details", {}).get("humidity")
    risk_level = risk.get("risk_level", "UNKNOWN")
    interpretation = (
        f"Current weather risk is {risk_level}. "
        f"Humidity is {humidity}% when available. "
        "Weather provides contextual information only and does not prove disease progression."
    )

    return {
        "available": True,
        "risk_level": risk_level,
        "risk_score": risk.get("risk_score"),
        "details": risk.get("details", {}),
        "alert": risk.get("alert"),
        "interpretation": interpretation,
        "raw": risk,
    }
