"""Unit tests — Nutrient Deficiency backend (Component 1)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND = PROJECT_ROOT / "Nutrient_Deficiency" / "backend"
sys.path.insert(0, str(BACKEND))

from utils.response_utils import fail, ok  # noqa: E402


@pytest.fixture
def app():
    return Flask(__name__)


class TestResponseUtils:
    def test_ok_with_data(self, app):
        with app.app_context():
            response, status = ok(data={"class": "Nitrogen"}, message="success")
            body = response.get_json()
        assert status == 200
        assert body["message"] == "success"
        assert body["data"]["class"] == "Nitrogen"

    def test_ok_without_data(self, app):
        with app.app_context():
            response, status = ok()
            body = response.get_json()
        assert status == 200
        assert body["message"] == "ok"
        assert "data" not in body

    def test_fail_custom_status(self, app):
        with app.app_context():
            response, status = fail("Invalid image", status=422)
            body = response.get_json()
        assert status == 422
        assert body["message"] == "Invalid image"


class TestClassNamesConfig:
    def test_class_names_file_exists_and_valid_json(self):
        class_path = BACKEND / "model" / "disease_class_names.json"
        if not class_path.is_file():
            pytest.skip("Model class names file not present on this machine")
        names = json.loads(class_path.read_text(encoding="utf-8"))
        assert isinstance(names, list)
        assert len(names) >= 1
        assert all(isinstance(n, str) for n in names)
