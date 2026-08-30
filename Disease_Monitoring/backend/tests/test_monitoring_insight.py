"""Monitoring insight explanation-layer tests."""

from utils.monitoring_insight import (
    _template_insight,
    build_insight_payload,
    generate_farmer_insight,
)


def test_payload_uses_given_scores_only():
    payload = build_insight_payload(
        crop_part="LEAF",
        overall_status="IMPROVING",
        monitoring_summary={
            "initial_severity_pct": 18.0,
            "peak_severity_pct": 24.0,
            "final_severity_pct": 12.0,
            "overall_change_pct": -6.0,
            "overall_trend": "IMPROVING",
            "severity_timeline": "18% → 24% → 12%",
            "peak_observation_number": 2,
            "observation_count": 3,
        },
        observations_summary=[
            {"severity_score": 0.18, "severity_class": "LOW", "trend": "BASELINE"},
            {"severity_score": 0.24, "severity_class": "LOW", "trend": "WORSENING"},
            {"severity_score": 0.12, "severity_class": "LOW", "trend": "IMPROVING"},
        ],
    )
    assert payload["initial_severity_pct"] == 18.0
    assert payload["final_severity_pct"] == 12.0
    assert payload["observations"][1]["severity_pct"] == 24.0


def test_template_insight_has_no_provider_branding():
    text = _template_insight(
        {
            "crop_part": "LEAF",
            "overall_trend": "STABLE",
            "initial_severity_pct": 20,
            "final_severity_pct": 19,
            "overall_change_pct": -1,
            "peak_severity_pct": 20,
            "peak_observation_number": 1,
            "severity_timeline": "20% → 19%",
            "observation_count": 2,
        }
    ).lower()
    assert "gemini" not in text
    assert "google" not in text
    assert "api" not in text
    assert "20" in text
    assert "19" in text
    # Keep it short for farmers
    assert len(text) < 280
    assert "timeline" not in text
    assert "peak" not in text


def test_generate_falls_back_to_template(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    insight = generate_farmer_insight(
        {
            "crop_part": "FRUIT",
            "overall_trend": "WORSENING",
            "initial_severity_pct": 10,
            "final_severity_pct": 40,
            "overall_change_pct": 30,
            "peak_severity_pct": 40,
            "peak_observation_number": 3,
            "severity_timeline": "10% → 20% → 40%",
            "observation_count": 3,
        }
    )
    assert insight["available"] is True
    assert insight["source"] == "template"
    assert "Monitoring insight" == insight["title"]
    assert "worse" in insight["text"].lower()
    assert len(insight["text"]) < 280