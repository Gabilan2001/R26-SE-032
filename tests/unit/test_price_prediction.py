"""Unit tests — Price Prediction backend (Component 4)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND = PROJECT_ROOT / "price_prediction" / "backend"
sys.path.insert(0, str(BACKEND))

from app.config.locations import list_known_location_labels, resolve_location  # noqa: E402
from app.services.news_impact_service import _detect_topics, _score_direction  # noqa: E402
from app.utils.feature_utils import normalize_prices  # noqa: E402


class TestFeatureUtils:
    def test_normalize_prices_range(self):
        assert normalize_prices([100, 150, 200]) == [0.0, 0.5, 1.0]

    def test_normalize_prices_flat_values(self):
        assert normalize_prices([5, 5, 5]) == [0.0, 0.0, 0.0]

    def test_normalize_prices_empty(self):
        assert normalize_prices([]) == []


class TestLocations:
    def test_resolve_known_location_dambulla(self):
        geo = resolve_location("Dambulla")
        assert geo.display_name == "Dambulla"
        assert geo.latitude == 7.8600

    def test_resolve_unknown_preserves_label_with_default_coords(self):
        geo = resolve_location("Unknown Village")
        assert geo.display_name == "Unknown Village"
        assert geo.latitude == 7.8600

    def test_resolve_empty_uses_default(self):
        geo = resolve_location("")
        assert "Dambulla" in geo.display_name

    def test_known_labels_non_empty(self):
        labels = list_known_location_labels()
        assert "Colombo" in labels
        assert "Dambulla" in labels


class TestNewsImpactService:
    def test_drought_headline_scores_increase(self):
        blob = "sri lanka drought hits tomato farms and reduces harvest"
        direction, topics = _score_direction(blob)
        assert direction == "increase"
        assert "drought" in topics

    def test_surplus_headline_scores_decrease(self):
        blob = "record harvest surplus lowers vegetable prices in wholesale market"
        direction, topics = _score_direction(blob)
        assert direction == "decrease"

    def test_neutral_unrelated_text(self):
        direction, _ = _score_direction("local cricket match results today")
        assert direction == "neutral"

    def test_detect_topics_fuel_price(self):
        topics = _detect_topics("fuel price hike impacts agricultural transport")
        assert "fuel_price" in topics
