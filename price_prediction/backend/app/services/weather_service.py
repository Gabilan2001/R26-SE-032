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

import os
import time

logger = logging.getLogger(__name__)

OPEN_METEO_URL = os.getenv("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")
OPEN_METEO_SEASONAL_URL = os.getenv("OPEN_METEO_SEASONAL_URL", "https://seasonal-api.open-meteo.com/v1/seasonal")

# Treat tiny floating noise as zero rain when checking for drought.
DRY_MM_THRESHOLD = 0.05

# In-memory cache for SEAS5 ensemble responses: key -> (timestamp, data)
_SEAS5_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 6 * 3600  # 6 Hours TTL



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
) -> Tuple[str, str, float, str, str, str, float, float, float, str, str, str, Dict[str, Any]]:
    """
    Apply agricultural weather & water-stress evaluation rules for the named area.

    Evaluates both excess water and water-stress / drought conditions with time-lag awareness.
    """
    if not daily_rain or not dates:
        raise ValueError("Open-Meteo returned no usable daily rows.")

    total_rainfall = sum(daily_rain)
    avg_daily_rain = total_rainfall / len(daily_rain)
    max_daily_rain = max(daily_rain)
    expected_temperature_celsius = sum(daily_temp_mid) / len(daily_temp_mid)
    max_temp = max(daily_temp_mid)
    hum_vals = [h for h in daily_humidity if h > 0]
    avg_humidity = sum(hum_vals) / len(hum_vals) if hum_vals else 0.0

    dry_days_count = sum(1 for r in daily_rain if r <= DRY_MM_THRESHOLD)
    all_dry = dry_days_count == len(daily_rain)

    # 1. Excess-Water Conditions (Flooding, heavy rain, waterlogging)
    if max_daily_rain > 50 or total_rainfall > 150:
        signal = "heavy_rain_flood_risk"
        storm_risk = "high"
        score = 0.30
        price_effect = "UP"
        impact = "HIGH"
        water_stress = "EXCESS_WATER"
        heat_stress = "NORMAL"
        favourability = "EXCESS_WATER"
        time_horizon = "Immediate / Short-term (1-3 days)"
        reason = (
            f"Heavy rainfall (up to {max_daily_rain:.1f} mm) in {area_label} threatens field waterlogging, "
            f"fruit fungal disease, and physical harvesting disruptions (immediate short-term supply bottleneck)."
        )

    elif max_daily_rain > 20 or total_rainfall > 60:
        signal = "moderate_rain_wet_stress"
        storm_risk = "moderate"
        score = 0.55
        price_effect = "SLIGHTLY_UP"
        impact = "MEDIUM"
        water_stress = "EXCESS_WATER"
        heat_stress = "NORMAL"
        favourability = "MODERATE"
        time_horizon = "Short-term (2-5 days)"
        reason = (
            f"Moderate rain (up to {max_daily_rain:.1f} mm) near {area_label} may slow fieldwork, "
            f"complicate transport, and slightly shorten tomato post-harvest shelf life."
        )

    # 2. Severe Water-Stress & Heat Conditions (Drought in Dry Zone / Low country)
    elif (all_dry or dry_days_count >= len(daily_rain) - 1) and (max_temp >= 35.0 or expected_temperature_celsius >= 33.0):
        signal = "severe_drought_heat_stress"
        storm_risk = "high"
        score = 0.35
        price_effect = "UP"
        impact = "HIGH"
        water_stress = "SEVERE_DROUGHT"
        heat_stress = "EXTREME_HEAT"
        favourability = "UNFAVOURABLE"
        time_horizon = "Medium to Long-term (14-60 days)"
        reason = (
            f"Prolonged dry spell combined with extreme heat (up to {max_temp:.1f}°C) around {area_label}. "
            f"Depleted soil moisture and high evapotranspiration stress irrigation tanks, posing risk to "
            f"nursery establishment and future planted area (medium/long-term supply pressure)."
        )

    elif all_dry and expected_temperature_celsius >= 31.0:
        signal = "drought_water_stress"
        storm_risk = "moderate"
        score = 0.48
        price_effect = "SLIGHTLY_UP"
        impact = "MEDIUM"
        water_stress = "MODERATE_STRESS"
        heat_stress = "MODERATE_HEAT"
        favourability = "WATER_STRESS"
        time_horizon = "Medium-term (7-21 days)"
        reason = (
            f"Dry spell near {area_label} with elevated temperatures ({expected_temperature_celsius:.1f}°C). "
            f"While current harvesting continues normally, persistent dry conditions may strain field irrigation "
            f"reserves over the coming weeks."
        )

    # 3. Favourable Mild Dry / Balanced Conditions
    elif max_daily_rain <= 5.0 and expected_temperature_celsius < 31.0:
        signal = "favourable_dry"
        storm_risk = "low"
        score = 0.85
        price_effect = "STABLE"
        impact = "NONE"
        water_stress = "NORMAL"
        heat_stress = "NORMAL"
        favourability = "FAVOURABLE"
        time_horizon = "Immediate to Medium-term"
        reason = (
            f"Mild dry conditions with moderate temperatures ({expected_temperature_celsius:.1f}°C) near {area_label}. "
            f"Favourable for active picking, grading, and wholesale distribution; routine irrigation remains sufficient."
        )

    else:
        # Balanced light/moderate showers
        signal = "favourable_balanced_moisture"
        storm_risk = "low"
        score = 0.80
        price_effect = "STABLE"
        impact = "LOW"
        water_stress = "NORMAL"
        heat_stress = "NORMAL"
        favourability = "FAVOURABLE"
        time_horizon = "Short to Medium-term"
        reason = (
            f"Balanced moisture conditions ({max_daily_rain:.1f} mm max rain) in {area_label} supporting crop "
            f"foliage and fruit set without causing harvesting delays."
        )

    agricultural_impact = {
        "location": area_label,
        "weather_condition": signal.replace("_", " ").title(),
        "rainfall_status": f"Max: {max_daily_rain:.1f} mm, Total: {total_rainfall:.1f} mm in {len(dates)} days",
        "heat_status": f"Avg: {expected_temperature_celsius:.1f}°C, Max: {max_temp:.1f}°C",
        "water_stress": water_stress,
        "heat_stress": heat_stress,
        "agricultural_stress": "High" if impact == "HIGH" else ("Moderate" if impact == "MEDIUM" else "Low"),
        "cultivation_favourability": favourability,
        "tomato_supply_risk": "Potential future risk" if water_stress == "SEVERE_DROUGHT" else ("Immediate harvest disruption" if water_stress == "EXCESS_WATER" else "Low / Normal"),
        "price_direction": "Potential upward pressure" if price_effect in ("UP", "SLIGHTLY_UP") else "Stable baseline",
        "time_horizon": time_horizon,
        "confidence": "High" if len(dates) >= 7 else "Medium",
        "evidence_type": "Direct meteorological forecast",
        "future_data_sources_needed": [
            "soil_moisture_active_depth_sensor",
            "minor_irrigation_tank_capacity_pct",
            "crop_evapotranspiration_et0_index",
        ],
    }

    return (
        signal,
        storm_risk,
        score,
        price_effect,
        reason,
        impact,
        max_daily_rain,
        expected_temperature_celsius,
        avg_humidity,
        water_stress,
        heat_stress,
        favourability,
        agricultural_impact,
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
        water_stress_level="NORMAL",
        heat_stress_level="NORMAL",
        agricultural_favourability="FAVOURABLE",
        agricultural_impact={
            "location": area_label,
            "status": "Weather data temporarily offline",
            "future_data_sources_needed": ["soil_moisture", "tank_levels", "evapotranspiration"],
        },
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
            water_stress,
            heat_stress,
            favourability,
            agri_impact,
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
            water_stress_level=water_stress,
            heat_stress_level=heat_stress,
            agricultural_favourability=favourability,
            agricultural_impact=agri_impact,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Open-Meteo weather fetch failed: %s", exc)
        return _fallback_response(location, area_label)


def fetch_seas5_seasonal_outlook(
    lat: float,
    lon: float,
    target_year: int,
    target_month: int,
) -> Optional[Dict[str, Any]]:
    """
    Fetch ECMWF SEAS5 50-member seasonal ensemble data from Open-Meteo for a given station.
    Aggregates daily precipitation per member across the target month (YYYY-MM).
    Returns None if target month is beyond available horizon or on request failure.
    """
    target_month_str = f"{target_year:04d}-{target_month:02d}"
    cache_key = f"{lat:.4f}_{lon:.4f}_{target_month_str}"

    # Check cache
    now = time.time()
    if cache_key in _SEAS5_CACHE:
        ts, cached_val = _SEAS5_CACHE[cache_key]
        if now - ts < CACHE_TTL_SECONDS:
            return cached_val

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,temperature_2m_mean",
        "models": "ecmwf_seas5",
    }

    try:
        resp = requests.get(OPEN_METEO_SEASONAL_URL, params=params, timeout=10)
        if resp.status_code != 200:
            logger.warning("SEAS5 API returned status %s", resp.status_code)
            return None

        data = resp.json()
        daily = data.get("daily", {})
        times = daily.get("time", [])
        if not times:
            return None

        # Check if target month is covered in returned times
        month_indices = [i for i, t in enumerate(times) if t.startswith(target_month_str)]
        if not month_indices:
            logger.info("Target month %s not covered by SEAS5 window (%s to %s)", target_month_str, times[0], times[-1])
            return None

        # Gather member precipitation sums for month_indices
        # Members are named precipitation_sum_member01 to member50
        member_sums: List[float] = []
        for m_num in range(1, 51):
            key = f"precipitation_sum_member{m_num:02d}"
            raw_series = daily.get(key)
            if raw_series and len(raw_series) >= len(times):
                m_sum = sum(_safe_float(raw_series[idx]) for idx in month_indices)
                member_sums.append(round(m_sum, 2))

        if not member_sums:
            raw_series = daily.get("precipitation_sum", [])
            if raw_series and len(raw_series) >= len(times):
                m_sum = sum(_safe_float(raw_series[idx]) for idx in month_indices)
                member_sums = [round(m_sum, 2)]

        # Mean temperature across the month
        temp_series = daily.get("temperature_2m_mean", [])
        avg_temp = 25.0
        if temp_series and len(temp_series) >= len(times):
            month_temps = [_safe_float(temp_series[idx]) for idx in month_indices]
            if month_temps:
                avg_temp = round(sum(month_temps) / len(month_temps), 2)

        result = {
            "target_month": target_month_str,
            "available_days": len(month_indices),
            "member_rainfall_sums": member_sums,
            "avg_temperature_celsius": avg_temp,
            "ensemble_members_count": len(member_sums),
        }

        _SEAS5_CACHE[cache_key] = (now, result)
        return result
    except Exception as exc:
        logger.warning("Failed to fetch SEAS5 seasonal outlook: %s", exc)
        return None

