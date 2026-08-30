"""Secondary visual severity verification — no live API."""

from utils.secondary_severity_verify import (
    STATUS_CONSISTENT,
    STATUS_INCONSISTENT,
    STATUS_UNAVAILABLE,
    compare_primary_to_secondary,
    verify_secondary_severity,
)


def test_compare_consistent():
    assert compare_primary_to_secondary("HIGH", "HIGH", available=True) == STATUS_CONSISTENT
    assert compare_primary_to_secondary("LOW", "low", available=True) == STATUS_CONSISTENT


def test_compare_inconsistent():
    assert compare_primary_to_secondary("LOW", "HIGH", available=True) == STATUS_INCONSISTENT


def test_compare_unavailable():
    assert compare_primary_to_secondary("HIGH", "HIGH", available=False) == STATUS_UNAVAILABLE
    assert compare_primary_to_secondary("HIGH", None, available=True) == STATUS_UNAVAILABLE


def test_verify_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    out = verify_secondary_severity(b"fake", "LEAF", "HIGH")
    assert out["verification_status"] == STATUS_UNAVAILABLE
    assert out["final_severity"] == "HIGH"
    assert out["secondary_severity"] is None


def test_verify_consistent_when_api_agrees(monkeypatch):
    monkeypatch.setattr(
        "utils.secondary_severity_verify._call_vision_api",
        lambda *_a, **_k: (
            {
                "estimated_affected_area_percentage": 42.0,
                "severity": "HIGH",
                "confidence": 0.9,
                "reasoning": "large lesions",
            },
            True,
        ),
    )
    out = verify_secondary_severity(b"x", "LEAF", "HIGH")
    assert out["verification_status"] == STATUS_CONSISTENT
    assert out["final_severity"] == "HIGH"
    assert out["secondary_severity"] == "HIGH"


def test_verify_inconsistent_keeps_primary(monkeypatch):
    monkeypatch.setattr(
        "utils.secondary_severity_verify._call_vision_api",
        lambda *_a, **_k: (
            {
                "estimated_affected_area_percentage": 10.0,
                "severity": "HIGH",
                "confidence": 0.8,
                "reasoning": "spots",
            },
            True,
        ),
    )
    out = verify_secondary_severity(b"x", "LEAF", "LOW")
    assert out["verification_status"] == STATUS_INCONSISTENT
    assert out["final_severity"] == "LOW"


def test_verify_invalid_json_unavailable(monkeypatch):
    monkeypatch.setattr(
        "utils.secondary_severity_verify._call_vision_api",
        lambda *_a, **_k: (None, False),
    )
    out = verify_secondary_severity(b"x", "FRUIT", "HIGH")
    assert out["verification_status"] == STATUS_UNAVAILABLE
    assert out["final_severity"] == "HIGH"
