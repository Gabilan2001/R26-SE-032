"""Unit tests — Disease Monitoring backend (Component 3)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND = PROJECT_ROOT / "Disease_Monitoring" / "backend"
sys.path.insert(0, str(BACKEND))

from observation.trend_analysis import (  # noqa: E402
    TREND_BASELINE,
    TREND_IMPROVING,
    TREND_STABLE,
    TREND_WORSENING,
    compute_overall_status,
    compute_trend,
)
from utils.location_service import public_location_fields, resolve_manual_location  # noqa: E402
from utils.weather_utils import compute_weather_risk_score  # noqa: E402


class TestLocationService:
    def test_resolve_manual_colombo(self):
        loc = resolve_manual_location("Colombo")
        assert loc["area"] == "Colombo"
        assert loc["district"] == "Colombo"
        assert loc["latitude"] == 6.9271

    def test_public_location_fields_whitelist(self):
        raw = {
            "latitude": 7.86,
            "longitude": 80.65,
            "area": "Dambulla",
            "district": "Matale",
            "province": "Central",
            "source": "manual",
            "internal_secret": "hidden",
        }
        public = public_location_fields(raw)
        assert "internal_secret" not in public
        assert public["area"] == "Dambulla"
        assert public["source"] == "manual"

    def test_public_location_fields_empty_input(self):
        assert public_location_fields(None) == {}


class TestTrendAnalysis:
    def test_compute_trend_baseline_when_no_previous(self):
        assert compute_trend(current_score=0.5, previous_score=None) == TREND_BASELINE

    def test_compute_trend_improving(self):
        # Above RECOVERED_SCORE_MAX (0.25) so delta maps to IMPROVING, not RECOVERED.
        assert compute_trend(current_score=0.35, previous_score=0.5) == TREND_IMPROVING

    def test_compute_trend_worsening(self):
        assert compute_trend(current_score=0.8, previous_score=0.3) == TREND_WORSENING

    def test_compute_trend_stable_within_epsilon(self):
        assert compute_trend(current_score=0.50, previous_score=0.51) == TREND_STABLE

    def test_compute_overall_status_empty(self):
        assert compute_overall_status([]) == TREND_BASELINE

    def test_compute_overall_status_latest_wins(self):
        assert compute_overall_status([TREND_BASELINE, TREND_IMPROVING]) == TREND_IMPROVING
        assert compute_overall_status([TREND_IMPROVING, TREND_WORSENING]) == TREND_WORSENING


class TestWeatherRiskScore:
    def test_missing_weather_returns_unknown(self):
        result = compute_weather_risk_score(None)
        assert result["risk_level"] == "UNKNOWN"
        assert result["risk_score"] == 0.0

    def test_high_humidity_produces_valid_level(self):
        result = compute_weather_risk_score(
            {"humidity": 85, "rainfall_1h": 5.0, "temperature": 28}
        )
        assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
        assert 0 <= result["risk_score"] <= 100

    def test_incomplete_weather_returns_unknown(self):
        result = compute_weather_risk_score({"humidity": 80})
        assert result["risk_level"] == "UNKNOWN"
