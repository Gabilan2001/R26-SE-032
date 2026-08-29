"""Weather snapshot tests — no live API calls."""

from observation.weather_context import fetch_weather_context


def test_no_location_does_not_block():
    wx = fetch_weather_context(None, None)
    assert wx["available"] is False
    assert wx["reason"] == "no_location"
    assert "location" in wx["interpretation"].lower()


def test_api_failure_is_graceful(monkeypatch):
    monkeypatch.setattr(
        "observation.weather_context.get_weather_risk",
        lambda lat, lon: {
            "risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "details": {},
        },
    )
    wx = fetch_weather_context(6.9, 79.8)
    assert wx["available"] is False
    assert wx["reason"] == "api_unavailable"


def test_success_snapshot_is_contextual(monkeypatch):
    monkeypatch.setattr(
        "observation.weather_context.get_weather_risk",
        lambda lat, lon: {
            "risk_score": 55.0,
            "risk_level": "MEDIUM",
            "alert": "Moderate weather-related disease pressure.",
            "details": {
                "humidity": 82,
                "temperature": 29,
                "rainfall_1h": 1.2,
                "wind_speed_kmh": 14,
                "dew_point": 25.4,
                "cloud_cover": 40,
            },
            "city": "Colombo",
            "timestamp": "2026-01-01T00:00:00",
        },
    )
    wx = fetch_weather_context(6.9271, 79.8612)
    assert wx["available"] is True
    assert wx["environmental_conditions"] == "Moderate"
    assert wx["details"]["rainfall"] == 1.2
    assert "humid" in wx["interpretation"].lower()
    assert "does not determine disease severity" in wx["interpretation"].lower()
    assert wx["disclaimer"]
