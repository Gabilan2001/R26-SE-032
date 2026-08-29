"""Severity trend analysis for observation sequences."""

from typing import Any, Dict, List, Optional

from config.observation_config import RECOVERED_SCORE_MAX, STABLE_EPSILON

TREND_IMPROVING = "IMPROVING"
TREND_STABLE = "STABLE"
TREND_WORSENING = "WORSENING"
TREND_RECOVERED = "RECOVERED"
TREND_BASELINE = "BASELINE"


def compute_trend(
    current_score: float,
    previous_score: Optional[float],
    recovered_score_max: float = RECOVERED_SCORE_MAX,
    stable_epsilon: float = STABLE_EPSILON,
) -> str:
    """
    Compare current relative severity score with the previous accepted observation.

    Uses observation-based relative pseudo-severity — not clinical recovery.
    """
    if previous_score is None:
        return TREND_BASELINE

    delta = current_score - previous_score

    if current_score <= recovered_score_max and current_score < previous_score:
        return TREND_RECOVERED

    if delta <= -stable_epsilon:
        return TREND_IMPROVING

    if delta >= stable_epsilon:
        return TREND_WORSENING

    return TREND_STABLE


def compute_overall_status(trends: list) -> str:
    """Derive overall case status from accepted observation trends (most recent wins)."""
    if not trends:
        return TREND_BASELINE
    latest = trends[-1]
    if latest == TREND_BASELINE:
        return TREND_STABLE
    return latest


def _score_to_pct(score: float) -> float:
    return round(float(score) * 100.0, 1)


def compute_monitoring_summary(severity_scores: List[float]) -> Optional[Dict[str, Any]]:
    """
    Summarise a completed or in-progress observation sequence.

    Uses stored severity scores only — no fabricated values.
    Overall trend compares final vs initial severity (observation-based, not clinical).
    """
    if not severity_scores:
        return None

    initial = float(severity_scores[0])
    final = float(severity_scores[-1])
    peak = max(float(s) for s in severity_scores)
    peak_index = severity_scores.index(peak) + 1

    initial_pct = _score_to_pct(initial)
    final_pct = _score_to_pct(final)
    peak_pct = _score_to_pct(peak)
    overall_change = round(final_pct - initial_pct, 1)

    if len(severity_scores) == 1:
        overall_trend = TREND_BASELINE
    else:
        overall_trend = compute_trend(final, initial)

    timeline_parts = [_score_to_pct(float(s)) for s in severity_scores]
    timeline = " → ".join(f"{p:g}%" for p in timeline_parts)

    day_labels = {1: 1, 2: 3, 3: 7}
    peak_day = day_labels.get(peak_index)
    peak_note = None
    if len(severity_scores) >= 1:
        if peak_day is not None:
            peak_note = (
                f"Highest severity was on Observation {peak_index} "
                f"(Day {peak_day}): {peak_pct:g}%."
            )
        else:
            peak_note = (
                f"Highest severity was on Observation {peak_index}: {peak_pct:g}%."
            )

    return {
        "initial_severity_pct": initial_pct,
        "peak_severity_pct": peak_pct,
        "final_severity_pct": final_pct,
        "overall_change_pct": overall_change,
        "overall_trend": overall_trend,
        "peak_observation_number": peak_index,
        "severity_timeline": timeline,
        "peak_note": peak_note,
        "observation_count": len(severity_scores),
    }
