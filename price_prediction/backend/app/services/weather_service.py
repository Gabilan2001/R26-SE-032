"""
Real weather signals using the free Open-Meteo forecast API (no API key).

Coordinates come from app.config.locations based on the user's location label.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import requests

from app.config.locations import resolve_location
from app.schemas.weather_schema import WeatherResponse

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Treat tiny floating noise as zero rain when checking for drought.
DRY_MM_THRESHOLD = 0.05


def _safe_float(value: Any) -> float:
    """Turn API values (including None) into a safe float for math."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fetch_open_meteo_payload(lat: float, lon: float, forecast_days: int) -> Dict[str, Any]:
    """Call Open-Meteo and return the JSON body, or raise on failure."""
    days = max(1, min(int(forecast_days), 16))
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": (
            "precipitation_sum,temperature_2m_max,temperature_2m_min,"
            "relative_humidity_2m_mean"
        ),
        "timezone": "Asia/Colombo",
        "forecast_days": days,
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=8)
    response.raise_for_status()
    return response.json()


def _parse_daily_series(
    payload: Dict[str, Any],
) -> Tuple[List[str], List[float], List[float], List[float]]:
    """
    Read dates, rain (mm), mid temperature (°C), and daily mean humidity (%) if present.

    Returns parallel lists (capped by API length).
    """
    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    rain_raw = daily.get("precipitation_sum") or []
    tmax_raw = daily.get("temperature_2m_max") or []
    tmin_raw = daily.get("temperature_2m_min") or []
    hum_raw = daily.get("relative_humidity_2m_mean") or []

    rains: List[float] = []
    temps_mid: List[float] = []
    hums: List[float] = []

    n = min(len(dates), len(rain_raw), len(tmax_raw), len(tmin_raw))
    if hum_raw:
        n = min(n, len(hum_raw))
    n = min(n, 16)
    for i in range(n):
        rain = _safe_float(rain_raw[i] if i < len(rain_raw) else 0.0)
        t_hi = _safe_float(tmax_raw[i] if i < len(tmax_raw) else 0.0)
        t_lo = _safe_float(tmin_raw[i] if i < len(tmin_raw) else 0.0)
        rains.append(rain)
        temps_mid.append((t_hi + t_lo) / 2.0)
        if i < len(hum_raw) and hum_raw:
            hums.append(_safe_float(hum_raw[i]))
        else:
            hums.append(0.0)

    return dates[:n], rains, temps_mid, hums[:n]


def _classify_weather(
    area_label: str,
    dates: List[str],
    daily_rain: List[float],
    daily_temp_mid: List[float],
    daily_humidity: List[float],
) -> Tuple[str, str, float, str, str, str, float, float, float]:
    """
    Apply rainfall rules for the named area.

    Returns:
        weather_signal, storm_risk_level, market_impact_score, price_effect,
        reason, impact, summary_rain_metric, expected_temperature_celsius, avg_humidity
    """
    if not daily_rain or not dates:
        raise ValueError("Open-Meteo returned no usable daily rows.")

    total_rainfall = sum(daily_rain)
    avg_daily_rain = total_rainfall / len(daily_rain)
    max_daily_rain = max(daily_rain)
    logger.debug(
        "Open-Meteo [%s] rain: total=%.2fmm avg=%.2fmm max=%.2fmm",
        area_label,
        total_rainfall,
        avg_daily_rain,
        max_daily_rain,
    )

    drought = all(r <= DRY_MM_THRESHOLD for r in daily_rain)
    expected_temperature_celsius = sum(daily_temp_mid) / len(daily_temp_mid)
    hum_vals = [h for h in daily_humidity if h > 0]
    avg_humidity = sum(hum_vals) / len(hum_vals) if hum_vals else 0.0

    if drought:
        return (
            "drought_risk",
            "high",
            0.35,
            "UP",
            (
                f"Prolonged dry spell around {area_label} may stress crops and "
                "tighten tomato supply later on."
            ),
            "HIGH",
            avg_daily_rain,
            expected_temperature_celsius,
            avg_humidity,
        )

    if max_daily_rain > 50:
        return (
            "heavy_rain",
            "high",
            0.30,
            "UP",
            (
                f"Heavy rainfall is expected near {area_label}, which can delay harvests "
                "and push tomato prices up."
            ),
            "HIGH",
            max_daily_rain,
            expected_temperature_celsius,
            avg_humidity,
        )
    if max_daily_rain > 20:
        return (
            "moderate_rain",
            "moderate",
            0.55,
            "SLIGHTLY_UP",
            f"Moderate rain near {area_label} may slow transport and affect supply.",
            "MEDIUM",
            max_daily_rain,
            expected_temperature_celsius,
            avg_humidity,
        )
    if max_daily_rain > 5:
        return (
            "light_rain",
            "low",
            0.70,
            "STABLE",
            f"Light rain near {area_label}; only a small effect on tomato supply is expected.",
            "LOW",
            max_daily_rain,
            expected_temperature_celsius,
            avg_humidity,
        )

    return (
        "dry",
        "low",
        0.85,
        "STABLE",
        f"Dry conditions near {area_label}; harvest and transport should stay closer to normal.",
        "NONE",
        max_daily_rain,
        expected_temperature_celsius,
        avg_humidity,
    )


def _fallback_response(location: str, area_label: str) -> WeatherResponse:
    """Safe response when Open-Meteo cannot be reached."""
    return WeatherResponse(
        location=location,
        weather_signal="unknown",
        expected_temperature_celsius=25.0,
        storm_risk_level="moderate",
        market_impact_score=0.60,
        price_effect="STABLE",
        reason="Weather data temporarily unavailable.",
        data_source="fallback",
        forecast_dates=[],
        daily_rainfall=[],
        impact="UNKNOWN",
        humidity_avg_pct=None,
        area_used_for_forecast=area_label,
    )


def fetch_weather_signal(location: str, forecast_days: int = 7) -> WeatherResponse:
    """
    Build a market-facing weather snapshot for the user's location label.

    Coordinates are resolved from the curated table (or a safe default).
    """
    geo = resolve_location(location)
    area_label = geo.display_name

    try:
        payload = _fetch_open_meteo_payload(geo.latitude, geo.longitude, forecast_days)
        dates, rains, temps_mid, hums = _parse_daily_series(payload)

        (
            signal,
            storm_risk,
            score,
            price_effect,
            reason,
            impact,
            _metric,
            expected_temp,
            avg_humidity,
        ) = _classify_weather(area_label, dates, rains, temps_mid, hums)

        return WeatherResponse(
            location=location,
            weather_signal=signal,
            expected_temperature_celsius=round(expected_temp, 2),
            storm_risk_level=storm_risk,
            market_impact_score=score,
            price_effect=price_effect,
            reason=reason,
            data_source="Open-Meteo API",
            forecast_dates=list(dates),
            daily_rainfall=[round(r, 2) for r in rains],
            impact=impact,
            humidity_avg_pct=round(avg_humidity, 1) if avg_humidity > 0 else None,
            area_used_for_forecast=area_label,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Open-Meteo weather fetch failed: %s", exc)
        return _fallback_response(location, area_label)
