from pydantic import BaseModel
from typing import Optional


class FruitUploadResponse(BaseModel):
    session_id:   str
    image_valid:  bool

    # Gate rejection
    rejection_reason: Optional[str] = None

    # ── U-Net multiclass segmentation ─────────────────────────────────────────
    severity:    float   # overall disease %  (metadata formula)
    confidence:  float   # mean predicted-class prob on disease pixels

    dominant_disease:            str    # "anthracnose" | "blossom_end_rot" | "spotted_wilt_virus" | "none" | "unknown"
    anthracnose_severity:        float  # % relative to (healthy + disease) pixels
    blossom_end_rot_severity:    float
    spotted_wilt_virus_severity: float
    healthy_percent:             float  # healthy pixels / total pixels * 100

    # ── Combined risk (UNet severity + weather) ───────────────────────────────
    combined_risk_score: float   # severity×0.6 + weather_risk×0.4  (0–100)
    weather_risk_score:  float   # OpenWeatherMap-derived score      (0–100)
    weather_risk_level:  str     # LOW | MEDIUM | HIGH | UNKNOWN (weather only)
    risk_level:          str     # final verdict: LOW | MEDIUM | HIGH | UNKNOWN

    # ── Weather alert message ─────────────────────────────────────────────────
    weather_alert: Optional[str] = None