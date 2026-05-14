"""
Resolve farmer / market locations to coordinates for Open-Meteo.

Known names use curated coordinates; unknown text still returns a best-effort
default (Dambulla area) so the API never breaks — the original label is kept
for display and news context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class GeoLocation:
    """A place name plus lat/lon used for weather forecasts."""

    display_name: str
    latitude: float
    longitude: float


# Major wholesale / growing hubs in Sri Lanka (approximate centres).
_LOCATION_TABLE: Dict[str, GeoLocation] = {
    "colombo": GeoLocation("Colombo", 6.9271, 79.8612),
    "dambulla": GeoLocation("Dambulla", 7.8600, 80.6500),
    "kandy": GeoLocation("Kandy", 7.2906, 80.6337),
    "nuwara eliya": GeoLocation("Nuwara Eliya", 6.9708, 80.7736),
    "galle": GeoLocation("Galle", 6.0329, 80.2160),
    "jaffna": GeoLocation("Jaffna", 9.6615, 80.0255),
    "kurunegala": GeoLocation("Kurunegala", 7.4806, 80.3621),
    "matara": GeoLocation("Matara", 5.9483, 80.5353),
    "badulla": GeoLocation("Badulla", 6.9934, 81.0550),
    "anuradhapura": GeoLocation("Anuradhapura", 8.3114, 80.4037),
    "batticaloa": GeoLocation("Batticaloa", 7.7102, 81.6924),
    "ratnapura": GeoLocation("Ratnapura", 6.6828, 80.3992),
}

# When the user types a place we do not recognise, we still return stable coords.
_DEFAULT_GEO = GeoLocation("Dambulla (default area)", 7.8600, 80.6500)


def list_known_location_labels() -> list[str]:
    """Labels for dropdowns (title case)."""
    return sorted({v.display_name for v in _LOCATION_TABLE.values()})


def resolve_location(user_input: str) -> GeoLocation:
    """
    Map free text or dropdown value to coordinates.

    Matching is case-insensitive; partial substring matches known keys.
    """
    raw = (user_input or "").strip()
    if not raw:
        return _DEFAULT_GEO

    key = raw.casefold()
    if key in _LOCATION_TABLE:
        return _LOCATION_TABLE[key]

    for canon, geo in _LOCATION_TABLE.items():
        if canon in key or key in canon:
            return geo

    # Allow "NuwaraEliya" style
    collapsed = key.replace(" ", "")
    for canon, geo in _LOCATION_TABLE.items():
        if collapsed == canon.replace(" ", ""):
            return geo

    # Preserve the user's wording for UI, but anchor weather to default hub.
    return GeoLocation(raw.title(), _DEFAULT_GEO.latitude, _DEFAULT_GEO.longitude)
