import logging

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from ml.predict.gate_predictor import is_valid_fruit
from ml.predict.unet_predictor import get_fruit_multiclass_severity
from utils.weather_utils import get_weather_risk

logger = logging.getLogger(__name__)

# ── Combined risk thresholds ──────────────────────────────────────────────────
#   combined_score = severity(%) × 0.6 + weather_risk_score(0-100) × 0.4
_COMBINED_HIGH   = 55.0
_COMBINED_MEDIUM = 25.0


def _compute_combined_risk(severity: float, weather: dict) -> dict:
    """
    Merge UNet disease severity with OpenWeatherMap risk score.

    Formula (weighted):
        combined_score = (severity × 0.6) + (weather_risk_score × 0.4)

    Override rules:
        • severity > 50  → always HIGH  (severe infection, weather irrelevant)
        • weather HIGH + any disease detected → minimum MEDIUM (spread risk)

    Returns dict with:
        combined_risk_score, weather_risk_score, weather_risk_level, risk_level
    """
    w_score = weather.get("risk_score", 0.0)
    w_level = weather.get("risk_level", "UNKNOWN")

    combined_score = round(severity * 0.6 + w_score * 0.4, 2)

    # ── Determine final risk level ────────────────────────────────────────────
    if severity > 50:
        # Severe infection → always HIGH regardless of weather
        risk_level = "HIGH"

    elif combined_score >= _COMBINED_HIGH:
        risk_level = "HIGH"

    elif combined_score >= _COMBINED_MEDIUM:
        risk_level = "MEDIUM"

    elif w_level == "HIGH" and severity > 0:
        # Low disease but dangerous weather → elevate to MEDIUM (spread risk)
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    logger.debug(
        "Combined risk: severity=%.2f%%, w_score=%.2f, w_level=%s → "
        "combined_score=%.2f, risk_level=%s",
        severity, w_score, w_level, combined_score, risk_level,
    )

    return {
        "combined_risk_score": combined_score,
        "weather_risk_score":  w_score,
        "weather_risk_level":  w_level,
        "risk_level":          risk_level,
    }


# ── Rejection response helper ─────────────────────────────────────────────────
def _rejection_response(session_id: str, reason: str) -> dict:
    return {
        "session_id":                  session_id,
        "image_valid":                 False,
        "rejection_reason":            reason,
        "severity":                    0.0,
        "confidence":                  0.0,
        "dominant_disease":            "none",
        "anthracnose_severity":        0.0,
        "blossom_end_rot_severity":    0.0,
        "spotted_wilt_virus_severity": 0.0,
        "healthy_percent":             0.0,
        "combined_risk_score":         0.0,
        "weather_risk_score":          0.0,
        "weather_risk_level":          "UNKNOWN",
        "risk_level":                  "UNKNOWN",
        "weather_alert":               None,
    }


# ── Main entry point ──────────────────────────────────────────────────────────
async def process_upload(
    file: UploadFile,
    session_id: str,
    lat: float,
    lon: float,
) -> dict:
    image_bytes = await file.read()

    # Step 1 — Gate: confirm the image is a tomato fruit
    valid, gate_conf, reason = is_valid_fruit(image_bytes)
    logger.debug(
        "Gate check session=%s: valid=%s conf=%.4f reason=%s",
        session_id, valid, gate_conf, reason,
    )
    if not valid:
        return _rejection_response(session_id, reason)

    # Step 2 — Multiclass U-Net inference (CPU-bound → threadpool)
    unet = await run_in_threadpool(get_fruit_multiclass_severity, image_bytes)
    logger.debug("UNet result session=%s: %s", session_id, unet)

    # Step 3 — Weather risk (OpenWeatherMap)
    weather = get_weather_risk(lat, lon)
    logger.debug("Weather risk session=%s: %s", session_id, weather)

    # Step 4 — Combined risk assessment
    risk = _compute_combined_risk(unet["severity"], weather)

    print(
        f"[RISK] session={session_id} | "
        f"disease_severity={unet['severity']}% | "
        f"weather_risk_score={risk['weather_risk_score']} ({risk['weather_risk_level']}) | "
        f"combined_score={risk['combined_risk_score']} → {risk['risk_level']}"
    )

    return {
        "session_id":                  session_id,
        "image_valid":                 True,
        "rejection_reason":            None,

        # U-Net results
        "severity":                    unet["severity"],
        "confidence":                  unet["confidence"],
        "dominant_disease":            unet["dominant_disease"],
        "anthracnose_severity":        unet["anthracnose_severity"],
        "blossom_end_rot_severity":    unet["blossom_end_rot_severity"],
        "spotted_wilt_virus_severity": unet["spotted_wilt_virus_severity"],
        "healthy_percent":             unet["healthy_percent"],

        # Combined risk
        "combined_risk_score":         risk["combined_risk_score"],
        "weather_risk_score":          risk["weather_risk_score"],
        "weather_risk_level":          risk["weather_risk_level"],
        "risk_level":                  risk["risk_level"],      # final verdict

        # Weather alert message
        "weather_alert":               weather.get("alert"),
    }
