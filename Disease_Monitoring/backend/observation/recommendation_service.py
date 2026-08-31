"""
Disease-specific monitoring recommendations when trend is WORSENING.

Separate from severity prediction and from legacy medicine/RAG treatment logic.
Provides observation-based monitoring guidance only.
"""

from typing import Any, Dict, Optional

from observation.trend_analysis import TREND_WORSENING

# Monitoring guidance keyed by disease (not fungicide prescriptions)
MONITORING_GUIDANCE = {
    "early_blight": {
        "title": "Early Blight - worsening relative severity",
        "actions": [
            "Increase observation frequency for this case.",
            "Inspect nearby leaves on the same crop for spread patterns.",
            "Review recent weather: prolonged humidity can support continued development.",
            "Coordinate with the disease-identification component if symptoms change.",
        ],
    },
    "late_blight": {
        "title": "Late Blight - worsening relative severity",
        "actions": [
            "Increase observation frequency and capture additional leaf images.",
            "Check for rapid lesion expansion after rainfall or high humidity.",
            "Monitor adjacent plants in the same block for similar symptoms.",
            "Escalate to field inspection if relative severity continues to rise.",
        ],
    },
    "leaf_miner": {
        "title": "Leaf Miner - worsening relative severity",
        "actions": [
            "Look for new mining trails on recently expanded leaves.",
            "Increase observation cadence to detect spread between leaves.",
            "Document whether damage is expanding within the same plant canopy.",
        ],
    },
    "anthracnose": {
        "title": "Anthracnose - worsening relative severity",
        "actions": [
            "Inspect fruit clusters for new sunken lesions.",
            "Increase upload frequency to track lesion expansion.",
            "Note post-rain conditions in field records.",
        ],
    },
    "blossom_end_rot": {
        "title": "Blossom End Rot - worsening relative severity",
        "actions": [
            "Monitor fruit set and irrigation consistency in field notes.",
            "Capture additional fruit images from the same case over time.",
            "Track whether affected fruit count appears to increase.",
        ],
    },
    "spotted_wilt_virus": {
        "title": "Spotted Wilt Virus - worsening relative severity",
        "actions": [
            "Inspect neighbouring fruit and leaves for ring-spot patterns.",
            "Increase observation frequency to document spread within the crop block.",
            "Coordinate with the external disease-identification component for confirmation.",
        ],
    },
}


def get_worsening_recommendation(
    disease: str,
    trend: str,
    weather_context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Return monitoring recommendation only when trend is WORSENING."""
    if trend != TREND_WORSENING:
        return None

    guidance = MONITORING_GUIDANCE.get(disease)
    if not guidance:
        guidance = {
            "title": f"{disease} - worsening relative severity",
            "actions": [
                "Increase observation frequency for this monitoring case.",
                "Capture additional images from the same crop area.",
            ],
        }

    result = dict(guidance)
    if weather_context and weather_context.get("available"):
        result["weather_context"] = weather_context.get("interpretation")
    return result
