"""
Location resolution for observation uploads.

GPS coordinates are reverse-geocoded (OpenWeather). Manual labels use a curated
Sri Lanka lookup table (same pattern as price_prediction).
"""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY") or os.getenv("OPENWEATHER_API_KEY", "")
REVERSE_GEO_URL = "https://api.openweathermap.org/geo/1.0/reverse"


@dataclass(frozen=True)
class GeoPlace:
    display_name: str
    latitude: float
    longitude: float
    district: str
    province: str


# Major Sri Lanka hubs — district/province for farmer-facing labels.
_KNOWN: Dict[str, GeoPlace] = {
    "colombo": GeoPlace("Colombo", 6.9271, 79.8612, "Colombo", "Western Province"),
    "dambulla": GeoPlace("Dambulla", 7.8600, 80.6500, "Matale", "Central Province"),
    "kandy": GeoPlace("Kandy", 7.2906, 80.6337, "Kandy", "Central Province"),
    "nuwara eliya": GeoPlace(
        "Nuwara Eliya", 6.9708, 80.7736, "Nuwara Eliya", "Central Province"
    ),
    "galle": GeoPlace("Galle", 6.0329, 80.2160, "Galle", "Southern Province"),
    "jaffna": GeoPlace("Jaffna", 9.6615, 80.0255, "Jaffna", "Northern Province"),
    "kurunegala": GeoPlace(
        "Kurunegala", 7.4806, 80.3621, "Kurunegala", "North Western Province"
    ),
    "matara": GeoPlace("Matara", 5.9483, 80.5353, "Matara", "Southern Province"),
    "badulla": GeoPlace("Badulla", 6.9934, 81.0550, "Badulla", "Uva Province"),
    "anuradhapura": GeoPlace(
        "Anuradhapura", 8.3114, 80.4037, "Anuradhapura", "North Central Province"
    ),
    "batticaloa": GeoPlace(
        "Batticaloa", 7.7102, 81.6924, "Batticaloa", "Eastern Province"
    ),
    "ratnapura": GeoPlace(
        "Ratnapura", 6.6828, 80.3992, "Ratnapura", "Sabaragamuwa Province"
    ),
}

_DEFAULT = GeoPlace("Dambulla", 7.8600, 80.6500, "Matale", "Central Province")


def list_known_location_labels() -> List[str]:
    return sorted({p.display_name for p in _KNOWN.values()})


def resolve_manual_location(label: str) -> Dict[str, Any]:
    """Map farmer-selected or typed place name to coordinates + admin labels."""
    raw = (label or "").strip()
    if not raw:
        return _as_payload(_DEFAULT, source="manual")

    key = raw.casefold()
    if key in _KNOWN:
        return _as_payload(_KNOWN[key], source="manual")

    for canon, place in _KNOWN.items():
        if canon in key or key in canon:
            return _as_payload(place, source="manual")

    collapsed = key.replace(" ", "")
    for canon, place in _KNOWN.items():
        if collapsed == canon.replace(" ", ""):
            return _as_payload(place, source="manual")

    # Unknown label: keep wording, anchor coords to default hub for weather.
    custom = GeoPlace(
        raw.title(),
        _DEFAULT.latitude,
        _DEFAULT.longitude,
        _DEFAULT.district,
        _DEFAULT.province,
    )
    return _as_payload(custom, source="manual")


def reverse_geocode(latitude: float, longitude: float) -> Dict[str, Any]:
    """Reverse geocode GPS coords; falls back to coord-only record on API failure."""
    base = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "area": None,
        "district": None,
        "province": None,
        "source": "gps",
    }
    if not WEATHER_API_KEY:
        base["area"] = f"{latitude:.4f}, {longitude:.4f}"
        return base

    try:
        response = requests.get(
            REVERSE_GEO_URL,
            params={"lat": latitude, "lon": longitude, "limit": 1, "appid": WEATHER_API_KEY},
            timeout=5,
        )
        if response.status_code != 200:
            logger.debug("Reverse geocode failed status=%s", response.status_code)
            base["area"] = f"{latitude:.4f}, {longitude:.4f}"
            return base

        items = response.json()
        if not items:
            base["area"] = f"{latitude:.4f}, {longitude:.4f}"
            return base

        item = items[0]
        area = item.get("name") or item.get("local_names", {}).get("en")
        province = item.get("state")
        base["area"] = area or f"{latitude:.4f}, {longitude:.4f}"
        base["province"] = province
        # OpenWeather rarely returns district for LK — match known city if possible.
        matched = _match_known_by_name(area or "")
        if matched:
            base["district"] = matched.district
            if not base["province"]:
                base["province"] = matched.province
        return base
    except Exception as exc:
        logger.debug("Reverse geocode error: %s", exc)
        base["area"] = f"{latitude:.4f}, {longitude:.4f}"
        return base


def resolve_observation_location(
    *,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    area: Optional[str] = None,
    district: Optional[str] = None,
    province: Optional[str] = None,
    location_label: Optional[str] = None,
    location_source: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build persisted location for one observation upload.
    Does not block uploads when location is missing.
    """
    if latitude is not None and longitude is not None:
        resolved = reverse_geocode(latitude, longitude)
        if area:
            resolved["area"] = area.strip()
        if district:
            resolved["district"] = district.strip()
        if province:
            resolved["province"] = province.strip()
        if location_source:
            resolved["source"] = location_source.strip().lower()
        return resolved

    if location_label and location_label.strip():
        return resolve_manual_location(location_label)

    if any(v and str(v).strip() for v in (area, district, province)):
        return {
            "latitude": latitude,
            "longitude": longitude,
            "area": (area or "").strip() or None,
            "district": (district or "").strip() or None,
            "province": (province or "").strip() or None,
            "source": (location_source or "manual").strip().lower(),
        }

    return {
        "latitude": None,
        "longitude": None,
        "area": None,
        "district": None,
        "province": None,
        "source": "unknown",
    }


def _match_known_by_name(name: str) -> Optional[GeoPlace]:
    key = (name or "").casefold().strip()
    if not key:
        return None
    if key in _KNOWN:
        return _KNOWN[key]
    for canon, place in _KNOWN.items():
        if canon in key or key in canon or key == place.display_name.casefold():
            return place
    return None


def _as_payload(place: GeoPlace, *, source: str) -> Dict[str, Any]:
    data = asdict(place)
    return {
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "area": data["display_name"],
        "district": data["district"],
        "province": data["province"],
        "source": source,
    }


def public_location_fields(location: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Subset exposed on observation API responses."""
    if not location:
        return {}
    out = {}
    for key in ("latitude", "longitude", "area", "district", "province", "source"):
        val = location.get(key)
        if val is not None and val != "":
            out[key] = val
    return out
