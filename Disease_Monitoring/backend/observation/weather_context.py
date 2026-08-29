"""Contextual weather snapshot for each observation.

Weather is environmental context only. It never determines severity class.
API failures and missing location must not block observation save.
"""

from typing import Any, Dict, Optional

from utils.weather_utils import get_weather_risk

UNAVAILABLE_NO_LOCATION = (
    "Location was not provided, so weather was not retrieved for this observation."
)
UNAVAILABLE_API = "Weather data is temporarily unavailable."
CONTEXT_DISCLAIMER = (
    "Weather is environmental context only and does not determine disease severity."
)


def fetch_weather_context(lat: Optional[float], lon: Optional[float]) -> Dict[str, Any]:
    """Always return a snapshot dict. Observation upload must not crash on weather errors."""
    if lat is None or lon is None:
        return _unavailable("no_location", UNAVAILABLE_NO_LOCATION)

    try:
        risk = get_weather_risk(lat, lon)
    except Exception:
        return _unavailable("api_unavailable", UNAVAILABLE_API)

    if not risk or risk.get("risk_level") == "UNKNOWN" or not risk.get("details"):
        return _unavailable("api_unavailable", UNAVAILABLE_API, raw=risk)

    details = dict(risk.get("details") or {})
    # Farmer-facing aliases used by the UI
    if "rainfall" not in details:
        details["rainfall"] = details.get("rainfall_1h", 0.0)

    env = _environmental_conditions(risk.get("risk_level"))
    interpretation = _farmer_interpretation(details, env)

    return {
        "available": True,
        "risk_level": risk.get("risk_level"),
        "risk_score": risk.get("risk_score"),
        "environmental_conditions": env,
        "details": details,
        "alert": risk.get("alert"),
        "city": risk.get("city"),
        "timestamp": risk.get("timestamp"),
        "interpretation": interpretation,
        "disclaimer": CONTEXT_DISCLAIMER,
        "raw": risk,
    }


def _unavailable(
    reason: str, interpretation: str, raw: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return {
        "available": False,
        "reason": reason,
        "interpretation": interpretation,
        "disclaimer": CONTEXT_DISCLAIMER,
        "details": {},
        "raw": raw,
    }


def _environmental_conditions(risk_level: Optional[str]) -> str:
    """Farmer label. Not a severity result."""
    mapping = {
        "HIGH": "Less Favourable",
        "MEDIUM": "Moderate",
        "LOW": "Favourable",
    }
    return mapping.get((risk_level or "").upper(), "Unknown")


def _farmer_interpretation(details: Dict[str, Any], env: str) -> str:
    humidity = details.get("humidity")
    rain = details.get("rainfall_1h")
    if rain is None:
        rain = details.get("rainfall") or 0
    cues = []
    try:
        if humidity is not None and float(humidity) >= 80:
            cues.append("relatively humid conditions")
        elif humidity is not None and float(humidity) >= 60:
            cues.append("moderate humidity")
    except (TypeError, ValueError):
        pass
    try:
        if rain is not None and float(rain) > 0:
            cues.append("recent rainfall")
    except (TypeError, ValueError):
        pass

    if cues:
        setting = " and ".join(cues)
        lead = f"This observation was recorded under {setting}."
    else:
        lead = f"Local weather conditions at this observation were {env.lower()}."

    return (
        f"{lead} Current weather context is {env}. {CONTEXT_DISCLAIMER}"
    )
