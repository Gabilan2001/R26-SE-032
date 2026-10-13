"""Unit tests — Tomato Fruit Disease backend (Component 2)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND = PROJECT_ROOT / "Tomato_fruit_disease" / "backend"
sys.path.insert(0, str(BACKEND))

from utils.response_utils import fail, ok  # noqa: E402


@pytest.fixture
def app():
    return Flask(__name__)


class TestResponseUtils:
    def test_ok_default(self, app):
        with app.app_context():
            response, status = ok(data={"class": "Anthracnose", "confidence": 91.2})
            body = response.get_json()
        assert status == 200
        assert body["data"]["class"] == "Anthracnose"

    def test_fail_default(self, app):
        with app.app_context():
            response, status = fail("No file uploaded")
            body = response.get_json()
        assert status == 400
        assert body["message"] == "No file uploaded"


class TestLowConfidenceRule:
    """Pure logic mirror of model_service.predict_image warning branch."""

    @staticmethod
    def _warning_for_confidence(confidence: float) -> str:
        if confidence < 70:
            return "Low confidence. Please retake photo with better lighting."
        return ""

    def test_below_threshold_shows_warning(self):
        assert self._warning_for_confidence(69.9) != ""

    def test_at_threshold_no_warning(self):
        assert self._warning_for_confidence(70.0) == ""

    def test_high_confidence_no_warning(self):
        assert self._warning_for_confidence(95.0) == ""
