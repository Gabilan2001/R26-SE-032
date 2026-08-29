"""Location resolution tests."""

from utils.location_service import resolve_manual_location, resolve_observation_location


def test_manual_colombo():
    loc = resolve_manual_location("Colombo")
    assert loc["area"] == "Colombo"
    assert loc["district"] == "Colombo"
    assert loc["province"] == "Western Province"
    assert loc["latitude"] == 6.9271


def test_gps_with_label_fallback():
    loc = resolve_observation_location(location_label="Kandy", location_source="manual")
    assert loc["area"] == "Kandy"
    assert loc["district"] == "Kandy"
    assert loc["source"] == "manual"


def test_missing_location_does_not_block():
    loc = resolve_observation_location()
    assert loc["source"] == "unknown"
    assert loc["area"] is None
