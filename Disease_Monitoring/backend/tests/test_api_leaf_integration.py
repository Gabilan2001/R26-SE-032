"""Leaf observation API integration tests (Fruit severity not required)."""

import io
import sys
from pathlib import Path

import pytest
from PIL import Image
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from main import app
from ml.predict.gate_predictor import reload_leaf_gate

client = TestClient(app)


def _jpeg_bytes(color=(40, 140, 50)) -> bytes:
    img = Image.new("RGB", (256, 256), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="module", autouse=True)
def _reload_gate():
    reload_leaf_gate()


def _early_blight_path() -> Path:
    return next((BACKEND / "datasets" / "PlantVillage" / "Tomato_Early_blight").glob("*.png"))


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_create_leaf_case_and_list_empty():
    res = client.post("/cases", json={"crop_part": "LEAF", "label": "api-leaf"})
    assert res.status_code == 200
    case_id = res.json()["case_id"]
    hist = client.get(f"/cases/{case_id}/observations")
    assert hist.status_code == 200
    assert hist.json()["observations"] == []


def test_leaf_upload_baseline_then_match(monkeypatch):
    # Bypass gate variability in CI; focus on observation pipeline
    monkeypatch.setattr(
        "observation.observation_service.is_valid_leaf",
        lambda _b: (True, 0.99, None),
    )
    case_id = client.post("/cases", json={"crop_part": "LEAF"}).json()["case_id"]
    img = _jpeg_bytes()
    files = {"file": ("leaf.jpg", img, "image/jpeg")}
    data = {"crop_part": "LEAF", "disease": "early_blight"}

    r1 = client.post(f"/cases/{case_id}/observations", data=data, files=files)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert body1["accepted"] is True
    assert body1["observation"]["consistency_status"] == "BASELINE"

    files2 = {"file": ("leaf.jpg", img, "image/jpeg")}
    r2 = client.post(f"/cases/{case_id}/observations", data=data, files=files2)
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert body2["accepted"] is True
    assert body2["observation"]["consistency_status"] == "MATCH"
    assert body2["observation"]["similarity_score"] >= 0.85
    assert body2["observation"]["trend"] in {"STABLE", "IMPROVING", "WORSENING", "RECOVERED", "BASELINE"}

    hist = client.get(f"/cases/{case_id}/observations").json()
    assert len(hist["observations"]) == 2

    status = client.get(f"/cases/{case_id}/status").json()
    assert status["observation_count"] == 2


def test_fruit_upload_succeeds_with_model(monkeypatch):
    from severity.fruit.fruit_severity import is_fruit_model_available

    if not is_fruit_model_available():
        pytest.skip("Fruit severity checkpoint not available")

    case_id = client.post("/cases", json={"crop_part": "FRUIT"}).json()["case_id"]
    files = {"file": ("fruit.jpg", _jpeg_bytes((180, 40, 40)), "image/jpeg")}
    data = {"crop_part": "FRUIT", "disease": "anthracnose"}
    import observation.observation_service as svc

    original = svc.is_valid_fruit
    svc.is_valid_fruit = lambda _b: (True, 0.99, None)
    try:
        res = client.post(f"/cases/{case_id}/observations", data=data, files=files)
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["accepted"] is True
        assert body["observation"]["severity_class"] in {"LOW", "HIGH"}
    finally:
        svc.is_valid_fruit = original


def test_fruit_upload_returns_503_without_model(monkeypatch):
    import observation.observation_service as svc
    import severity.fruit.fruit_severity as fruit_mod

    monkeypatch.setattr(fruit_mod, "FRUIT_SEVERITY_MODEL_PATH", "")
    monkeypatch.setattr(fruit_mod, "_model", None)

    case_id = client.post("/cases", json={"crop_part": "FRUIT"}).json()["case_id"]
    files = {"file": ("fruit.jpg", _jpeg_bytes((180, 40, 40)), "image/jpeg")}
    data = {"crop_part": "FRUIT", "disease": "anthracnose"}

    original = svc.is_valid_fruit
    svc.is_valid_fruit = lambda _b: (True, 0.99, None)
    try:
        res = client.post(f"/cases/{case_id}/observations", data=data, files=files)
        assert res.status_code == 503
        assert "Fruit" in res.text or "FRUIT" in res.text or "configured" in res.text.lower()
    finally:
        svc.is_valid_fruit = original


def test_improved_gate_accepts_early_blight_sample():
    path = _early_blight_path()
    from ml.predict.gate_predictor import is_valid_leaf

    ok, conf, reason = is_valid_leaf(path.read_bytes())
    assert ok is True, f"expected early blight leaf to pass gate, got conf={conf} reason={reason}"
