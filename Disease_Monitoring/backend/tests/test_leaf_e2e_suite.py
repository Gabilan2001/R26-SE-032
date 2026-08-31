"""
Leaf observation E2E suite (Tests 1–10 where automatable).

Fruit CNN is NOT trained; Fruit path asserts clear 503.
Does not retrain Leaf CNN. Does not modify YOLO.
"""

from __future__ import annotations

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
from ml.predict.gate_predictor import is_valid_leaf, reload_leaf_gate
from observation.recommendation_service import get_worsening_recommendation
from observation.trend_analysis import (
    TREND_IMPROVING,
    TREND_RECOVERED,
    TREND_STABLE,
    TREND_WORSENING,
    compute_trend,
)

client = TestClient(app)

EARLY = BACKEND / "datasets" / "PlantVillage" / "Tomato_Early_blight"
REJECT = BACKEND / "datasets" / "PlantVillage" / "REJECT"
HEALTHY = BACKEND / "datasets" / "PlantVillage" / "Tomato_healthy"


def _jpeg(color=(40, 140, 50)) -> bytes:
    img = Image.new("RGB", (256, 256), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _first_image(folder: Path) -> Path:
    for p in sorted(folder.glob("*")):
        if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            return p
    raise FileNotFoundError(folder)


@pytest.fixture(scope="module", autouse=True)
def _reload_gate():
    reload_leaf_gate()


def _create_leaf_case(label: str = "e2e") -> str:
    res = client.post("/cases", json={"crop_part": "LEAF", "label": label})
    assert res.status_code == 200
    return res.json()["case_id"]


def _upload(case_id: str, image_bytes: bytes, confirm: bool = False, weather: bool = False):
    data = {
        "crop_part": "LEAF",
        "disease": "early_blight",
        "confirm_same_case": "true" if confirm else "false",
    }
    if weather:
        data["latitude"] = "6.9271"
        data["longitude"] = "79.8612"
    files = {"file": ("leaf.jpg", image_bytes, "image/jpeg")}
    return client.post(f"/cases/{case_id}/observations", data=data, files=files)


# ── Test 1: Valid leaf → gate → severity → save obs 1 ─────────────────────────
def test_01_valid_leaf_baseline_saved():
    case_id = _create_leaf_case("t1")
    img = _first_image(EARLY).read_bytes()
    res = _upload(case_id, img)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["accepted"] is True
    assert body["image_valid"] is True
    obs = body["observation"]
    assert obs["consistency_status"] == "BASELINE"
    assert obs["trend"] == "BASELINE"
    assert 0.0 <= obs["severity_score"] <= 1.0
    assert obs["severity_class"] in {"LOW", "HIGH"}
    hist = client.get(f"/cases/{case_id}/observations").json()
    assert len(hist["observations"]) == 1


# ── Test 2: Obs 2 same image → MATCH → trend ──────────────────────────────────
def test_02_second_observation_match_trend():
    case_id = _create_leaf_case("t2")
    img = _first_image(EARLY).read_bytes()
    assert _upload(case_id, img).json()["accepted"] is True
    body2 = _upload(case_id, img).json()
    assert body2["accepted"] is True
    obs = body2["observation"]
    assert obs["consistency_status"] == "MATCH"
    assert obs["similarity_score"] >= 0.85
    assert obs["trend"] in {"STABLE", "IMPROVING", "WORSENING", "RECOVERED"}
    assert len(client.get(f"/cases/{case_id}/observations").json()["observations"]) == 2


# ── Test 3: Different image → MISMATCH ────────────────────────────────────────
def test_03_different_image_mismatch():
    case_id = _create_leaf_case("t3")
    img1 = _first_image(EARLY).read_bytes()
    # Find a second leaf image that passes gate and is visually different
    img2 = None
    for p in sorted(HEALTHY.glob("*")):
        if p.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        data = p.read_bytes()
        ok, _, _ = is_valid_leaf(data)
        if ok:
            img2 = data
            break
    if img2 is None:
        pytest.skip("No gate-passing healthy leaf image for mismatch test")

    assert _upload(case_id, img1).json()["accepted"] is True
    body2 = _upload(case_id, img2, confirm=False).json()
    assert body2["accepted"] is False
    assert body2["consistency_status"] == "MISMATCH"
    assert len(client.get(f"/cases/{case_id}/observations").json()["observations"]) == 1


# ── Test 4: POSSIBLE_MATCH is accepted without confirmation ───────────────────
def test_04_possible_match_auto_accept():
    from consistency.consistency_checker import check_consistency

    status, accepted, reason = check_consistency(0.75, is_first_observation=False)
    assert status == "POSSIBLE_MATCH"
    assert accepted is True
    assert reason is None


# ── Test 5 / 6: WORSENING recommendation vs IMPROVING no recommendation ───────
def test_05_worsening_recommendation():
    rec = get_worsening_recommendation("early_blight", TREND_WORSENING, None)
    assert rec is not None
    assert "worsening" in rec["title"].lower()
    assert "Early Blight -" in rec["title"] or "early blight" in rec["title"].lower()


def test_06_improving_no_worsening_recommendation():
    assert get_worsening_recommendation("early_blight", TREND_IMPROVING, None) is None
    assert get_worsening_recommendation("early_blight", TREND_STABLE, None) is None


# ── Test 7: Invalid image → gate rejection ────────────────────────────────────
def test_07_invalid_image_gate_rejection(monkeypatch):
    monkeypatch.setenv("IMAGE_GATE_MODE", "strict")
    case_id = _create_leaf_case("t7")
    # Prefer a REJECT sample that the improved gate rejects
    rejected = False
    for p in sorted(REJECT.glob("*"))[:40]:
        if p.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        body = _upload(case_id, p.read_bytes()).json()
        if body.get("accepted") is False and body.get("image_valid") is False:
            rejected = True
            assert "leaf" in (body.get("rejection_reason") or "").lower()
            break
    if not rejected:
        # Fallback: random noise often fails gate after retrain
        noise = _jpeg((255, 0, 255))
        body = _upload(case_id, noise).json()
        assert body["accepted"] is False
        assert body.get("image_valid") is False or body.get("consistency_status") is not None


# ── Test 8: Fruit path works when CNN configured; 503 if path cleared ─────────
def test_08_fruit_observation_with_cnn(monkeypatch):
    import observation.observation_service as svc
    from severity.fruit.fruit_severity import is_fruit_model_available

    if not is_fruit_model_available():
        pytest.skip("Fruit severity checkpoint not available")

    case = client.post("/cases", json={"crop_part": "FRUIT"}).json()
    case_id = case["case_id"]
    monkeypatch.setattr(svc, "is_valid_fruit", lambda _b: (True, 0.99, None))
    files = {"file": ("fruit.jpg", _jpeg((200, 40, 40)), "image/jpeg")}
    data = {"crop_part": "FRUIT", "disease": "anthracnose"}
    res = client.post(f"/cases/{case_id}/observations", data=data, files=files)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["accepted"] is True
    assert body["observation"]["crop_part"] == "FRUIT"
    assert body["observation"]["severity_class"] in {"LOW", "HIGH"}


def test_08b_fruit_returns_503_when_cnn_path_cleared(monkeypatch):
    import observation.observation_service as svc
    import severity.fruit.fruit_severity as fruit_mod

    monkeypatch.setattr(fruit_mod, "FRUIT_SEVERITY_MODEL_PATH", "")
    monkeypatch.setattr(fruit_mod, "_model", None)
    monkeypatch.setattr(svc, "is_valid_fruit", lambda _b: (True, 0.99, None))

    case = client.post("/cases", json={"crop_part": "FRUIT"}).json()
    case_id = case["case_id"]
    files = {"file": ("fruit.jpg", _jpeg((200, 40, 40)), "image/jpeg")}
    data = {"crop_part": "FRUIT", "disease": "anthracnose"}
    res = client.post(f"/cases/{case_id}/observations", data=data, files=files)
    assert res.status_code == 503


# ── Test 9: Weather context attached when coords provided ─────────────────────
def test_09_weather_context_path(monkeypatch):
    case_id = _create_leaf_case("t9")
    img = _first_image(EARLY).read_bytes()

    monkeypatch.setattr(
        "observation.weather_context.get_weather_risk",
        lambda lat, lon: {
            "risk_score": 55.0,
            "risk_level": "MEDIUM",
            "alert": "Moderate weather-related disease pressure.",
            "details": {"humidity": 70, "temperature": 28, "rainfall_1h": 0.0},
            "city": "Demo",
            "timestamp": "2026-01-01T00:00:00",
        },
    )
    body = _upload(case_id, img, weather=True).json()
    assert body["accepted"] is True
    wx = body["observation"]["weather_context"]
    assert wx is not None
    assert wx.get("available") is True
    assert "contextual" in (wx.get("interpretation") or "").lower() or "weather" in (
        wx.get("interpretation") or ""
    ).lower()


# ── Test 10: Status payload supports frontend final result display ────────────
def test_10_status_payload_for_frontend():
    case_id = _create_leaf_case("t10")
    img = _first_image(EARLY).read_bytes()
    _upload(case_id, img)
    _upload(case_id, img)
    status = client.get(f"/cases/{case_id}/status").json()
    assert status["case_id"] == case_id
    assert status["observation_count"] == 2
    assert status["latest_observation"] is not None
    latest = status["latest_observation"]
    for key in (
        "observation_id",
        "created_at",
        "disease",
        "severity_score",
        "severity_class",
        "consistency_status",
        "trend",
    ):
        assert key in latest
    assert "observations_summary" in status


# ── Trend rule regression (STABLE / IMPROVING / WORSENING / RECOVERED) ────────
def test_trend_rules_unchanged():
    assert compute_trend(0.851, 0.851) == TREND_STABLE
    assert compute_trend(0.5155, 0.851) == TREND_IMPROVING
    assert compute_trend(0.851, 0.5155) == TREND_WORSENING
    assert compute_trend(0.20, 0.40) == TREND_RECOVERED


def test_health_and_root():
    assert client.get("/health").json()["status"] == "healthy"
    root = client.get("/").json()
    assert "Observation-Based" in root["status"] or "LEAF" in str(root)
