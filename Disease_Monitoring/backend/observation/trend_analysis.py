"""Severity trend analysis for observation sequences."""

from typing import Optional

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
