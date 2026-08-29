"""Overall monitoring summary tests."""

from observation.trend_analysis import (
    TREND_BASELINE,
    TREND_IMPROVING,
    TREND_WORSENING,
    compute_monitoring_summary,
)


def test_empty_returns_none():
    assert compute_monitoring_summary([]) is None


def test_single_observation_baseline():
    summary = compute_monitoring_summary([0.18])
    assert summary["initial_severity_pct"] == 18.0
    assert summary["peak_severity_pct"] == 18.0
    assert summary["final_severity_pct"] == 18.0
    assert summary["overall_trend"] == TREND_BASELINE
    assert summary["severity_timeline"] == "18%"


def test_improving_sequence():
    # 35% → 40% → 28% — final below initial but above recovered threshold
    summary = compute_monitoring_summary([0.35, 0.40, 0.28])
    assert summary["initial_severity_pct"] == 35.0
    assert summary["peak_severity_pct"] == 40.0
    assert summary["final_severity_pct"] == 28.0
    assert summary["overall_change_pct"] == -7.0
    assert summary["overall_trend"] == TREND_IMPROVING
    assert summary["peak_observation_number"] == 2
    assert summary["severity_timeline"] == "35% → 40% → 28%"
    assert "Observation 2" in summary["peak_note"]


def test_recovered_overall():
    summary = compute_monitoring_summary([0.18, 0.24, 0.12])
    assert summary["overall_trend"] == "RECOVERED"
    assert summary["overall_change_pct"] == -6.0


def test_worsening_overall():
    summary = compute_monitoring_summary([0.18, 0.24, 0.30])
    assert summary["overall_trend"] == TREND_WORSENING
    assert summary["overall_change_pct"] == 12.0
