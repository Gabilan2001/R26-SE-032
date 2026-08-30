"""Visual consistency checking between observations."""

from typing import Optional, Tuple

from config.observation_config import MATCH_THRESHOLD, POSSIBLE_MATCH_THRESHOLD

CONSISTENCY_BASELINE = "BASELINE"
CONSISTENCY_MATCH = "MATCH"
CONSISTENCY_POSSIBLE_MATCH = "POSSIBLE_MATCH"
CONSISTENCY_MISMATCH = "MISMATCH"


def check_consistency(
    similarity_score: Optional[float],
    is_first_observation: bool,
    confirm_same_case: bool = False,
) -> Tuple[str, bool, Optional[str]]:
    """
    Determine consistency status and whether the observation may enter the case sequence.

    Returns:
        (consistency_status, accepted_into_sequence, rejection_reason)
    """
    if is_first_observation:
        return CONSISTENCY_BASELINE, True, None

    if similarity_score is None:
        return CONSISTENCY_MISMATCH, False, "Unable to compute similarity with previous observation."

    if similarity_score >= MATCH_THRESHOLD:
        return CONSISTENCY_MATCH, True, None

    if similarity_score >= POSSIBLE_MATCH_THRESHOLD:
        # Soft match — accept without a farmer confirm popup.
        return CONSISTENCY_POSSIBLE_MATCH, True, None

    if confirm_same_case:
        return CONSISTENCY_MISMATCH, True, None

    return (
        CONSISTENCY_MISMATCH,
        False,
        (
            "Visual consistency check failed. This image appears visually different from "
            "previous observations in this case. Start a new case or set confirm_same_case=true."
        ),
    )
