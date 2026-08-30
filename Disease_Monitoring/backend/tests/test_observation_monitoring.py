import io
import sys
import uuid
from pathlib import Path

import pytest
from PIL import Image

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from config.observation_config import (
    MATCH_THRESHOLD,
    POSSIBLE_MATCH_THRESHOLD,
    RECOVERED_SCORE_MAX,
    STABLE_EPSILON,
)
from consistency.consistency_checker import (
    CONSISTENCY_BASELINE,
    CONSISTENCY_MATCH,
    CONSISTENCY_MISMATCH,
    CONSISTENCY_POSSIBLE_MATCH,
    check_consistency,
)
from consistency.similarity import cosine_similarity, l2_normalize
from observation.observation_repository import (
    create_case,
    get_accepted_observations,
    get_last_accepted_observation,
    init_observation_db,
    insert_observation,
)
from observation.trend_analysis import (
    TREND_IMPROVING,
    TREND_RECOVERED,
    TREND_STABLE,
    TREND_WORSENING,
    compute_trend,
)
from severity.leaf.efficientnet_severity import is_leaf_model_available, predict_leaf_severity


def _solid_image(color=(120, 180, 90)) -> bytes:
    img = Image.new("RGB", (256, 256), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _init_db():
    init_observation_db()


def test_cosine_similarity_identical():
    v = l2_normalize([1.0, 2.0, 3.0])
    assert cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-6)


def test_consistency_baseline():
    status, accepted, reason = check_consistency(None, is_first_observation=True)
    assert status == CONSISTENCY_BASELINE
    assert accepted is True
    assert reason is None


def test_consistency_match():
    status, accepted, _ = check_consistency(MATCH_THRESHOLD + 0.05, is_first_observation=False)
    assert status == CONSISTENCY_MATCH
    assert accepted is True


def test_consistency_possible_match():
    mid = (MATCH_THRESHOLD + POSSIBLE_MATCH_THRESHOLD) / 2
    status, accepted, reason = check_consistency(mid, is_first_observation=False)
    assert status == CONSISTENCY_POSSIBLE_MATCH
    assert accepted is True
    assert reason is None


def test_consistency_mismatch_without_confirm():
    status, accepted, reason = check_consistency(0.1, is_first_observation=False)
    assert status == CONSISTENCY_MISMATCH
    assert accepted is False
    assert reason is not None


def test_consistency_mismatch_with_confirm():
    status, accepted, _ = check_consistency(0.1, is_first_observation=False, confirm_same_case=True)
    assert status == CONSISTENCY_MISMATCH
    assert accepted is True


def test_trend_improving_stable_worsening_recovered():
    assert compute_trend(0.55, 0.80) == TREND_IMPROVING
    assert compute_trend(0.62, 0.60, stable_epsilon=STABLE_EPSILON) == TREND_STABLE
    assert compute_trend(0.82, 0.60) == TREND_WORSENING
    assert compute_trend(0.20, 0.40, recovered_score_max=RECOVERED_SCORE_MAX) == TREND_RECOVERED


def test_leaf_severity_model_loading():
    if not is_leaf_model_available():
        pytest.skip("Leaf EfficientNet checkpoint not available")
    result = predict_leaf_severity(_solid_image())
    assert 0.0 <= result["severity_score"] <= 1.0
    assert result["severity_class"] in {"LOW", "HIGH"}
    assert len(result["embedding"]) == 1280


def test_fruit_model_available_when_checkpoint_present():
    from severity.fruit.fruit_severity import is_fruit_model_available, predict_fruit_severity

    if not is_fruit_model_available():
        pytest.skip("Fruit severity checkpoint not available")
    result = predict_fruit_severity(_solid_image())
    assert 0.0 <= result["severity_score"] <= 1.0
    assert result["severity_class"] in {"LOW", "HIGH"}
    assert len(result["embedding"]) == 1280


def test_fruit_model_reports_unavailable_when_path_cleared(monkeypatch):
    import severity.fruit.fruit_severity as fruit_mod

    monkeypatch.setattr(fruit_mod, "FRUIT_SEVERITY_MODEL_PATH", "")
    monkeypatch.setattr(fruit_mod, "_model", None)
    assert fruit_mod.is_fruit_model_available() is False


def test_append_only_observation_history():
    case = create_case("LEAF", label="test")
    case_id = case["case_id"]

    for i, score in enumerate([0.72, 0.55]):
        insert_observation(
            {
                "observation_id": f"OBS-TEST-{uuid.uuid4().hex[:8]}",
                "case_id": case_id,
                "crop_part": "LEAF",
                "created_at": f"2026-08-22T10:0{i}:00+00:00",
                "disease": "early_blight",
                "severity_score": score,
                "severity_class": "HIGH" if score >= 0.5 else "LOW",
                "embedding": [float(i)] * 1280,
                "similarity_score": None if i == 0 else 0.9,
                "consistency_status": "BASELINE" if i == 0 else "MATCH",
                "weather_context": None,
                "trend": "BASELINE" if i == 0 else TREND_IMPROVING,
                "status": "BASELINE" if i == 0 else TREND_IMPROVING,
                "recommendation": None,
                "accepted": True,
                "image_path": None,
            }
        )

    history = get_accepted_observations(case_id, "LEAF")
    assert len(history) == 2
    assert get_last_accepted_observation(case_id, "LEAF")["severity_score"] == 0.55


def test_leaf_fruit_history_separation():
    leaf_case = create_case("LEAF")["case_id"]
    fruit_case = create_case("FRUIT")["case_id"]

    insert_observation(
        {
            "observation_id": f"OBS-LEAF-{uuid.uuid4().hex[:8]}",
            "case_id": leaf_case,
            "crop_part": "LEAF",
            "created_at": "2026-08-22T10:00:00+00:00",
            "disease": "early_blight",
            "severity_score": 0.7,
            "severity_class": "HIGH",
            "embedding": [0.1] * 1280,
            "similarity_score": None,
            "consistency_status": "BASELINE",
            "weather_context": None,
            "trend": "BASELINE",
            "status": "BASELINE",
            "recommendation": None,
            "accepted": True,
            "image_path": None,
        }
    )
    insert_observation(
        {
            "observation_id": f"OBS-FRUIT-{uuid.uuid4().hex[:8]}",
            "case_id": fruit_case,
            "crop_part": "FRUIT",
            "created_at": "2026-08-22T10:00:00+00:00",
            "disease": "anthracnose",
            "severity_score": 0.6,
            "severity_class": "HIGH",
            "embedding": [0.9] * 1280,
            "similarity_score": None,
            "consistency_status": "BASELINE",
            "weather_context": None,
            "trend": "BASELINE",
            "status": "BASELINE",
            "recommendation": None,
            "accepted": True,
            "image_path": None,
        }
    )

    assert len(get_accepted_observations(leaf_case, "LEAF")) == 1
    assert len(get_accepted_observations(fruit_case, "FRUIT")) == 1
    assert get_last_accepted_observation(leaf_case, "FRUIT") is None
