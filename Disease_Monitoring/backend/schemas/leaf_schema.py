from pydantic import BaseModel
from typing import Optional, Dict, List, Any


# ── Upload response (per day) ─────────────────────────────────────────────────
class LeafUploadResponse(BaseModel):
    session_id:             str
    day:                    int
    image_valid:            bool

    # Gate rejection
    rejection_reason:       Optional[str]   = None

    # U-Net severity
    disease_a_severity:     float
    disease_b_severity:     float
    disease_a_confidence:   float
    disease_b_confidence:   float

    # Combined Risk Status (FIX: Added to match new service logic)
    combined_risk_score:    Optional[float] = None
    combined_risk_level:    Optional[str]   = None

    # Weather
    weather_risk_score:     Optional[float] = None
    weather_risk_level:     Optional[str]   = None
    weather_alert:          Optional[str]   = None
    weather_details:        Optional[Dict]  = None

    # Rule engine daily output
    daily_status:           Optional[str]       = None
    daily_alerts:           Optional[List[str]] = []

    # Daily RAG-based advice (FIX: Added to match new service logic)
    treatment_advice:       Optional[Dict[str, Any]] = None


# ── TRR response (after Day 7) ────────────────────────────────────────────────
class TRRResponse(BaseModel):
    session_id:             str

    # Per-disease TRR scores
    trr_disease_a:          float
    trr_disease_b:          float
    overall_trr:            float

    # Per-disease verdicts
    verdict_disease_a:      str
    verdict_disease_b:      str
    overall_verdict:        str             # SUCCESS | PARTIAL | FAILURE

    # Severity history
    day1_severity_a:        float
    day7_severity_a:        float
    day1_severity_b:        float
    day7_severity_b:        float

    # Weather context
    weather_caused_failure: bool

    # Recommended action
    action:                 str

    # RAG output (only populated on FAILURE)
    rag_triggered:          bool                    = False
    alternative_treatment:  Optional[Dict[str, Any]] = None
    failed_medicine:        Optional[str]           = None
    failed_class:           Optional[str]           = None
    disease_name:           Optional[str]           = None