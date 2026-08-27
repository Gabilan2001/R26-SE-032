import asyncio
import logging

from fastapi import UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from ml.predict.gate_predictor import is_valid_leaf
from ml.predict.unet_predictor import get_leaf_severity
from utils.weather_utils import get_weather_risk
from services.rule_engine import compute_daily_output, compute_trr
from services.rag_engine import get_alternative_treatment
from utils.db_utils import save_daily_data, get_session_history, get_all_uploaded_days

logger = logging.getLogger(__name__)

DISEASE_DETECTION_THRESHOLD = 10.0
CO_INFECTION_THRESHOLD = 20.0
DOMINANCE_RATIO = 1.5


def build_weather_details(weather: dict) -> dict:
    details = weather.get("details", {}) if weather else {}
    weather_details = {
        "temperature": details.get("temperature"),
        "humidity": details.get("humidity"),
        "wind_speed": details.get("wind_speed"),
        "rainfall": details.get("rainfall_1h", 0.0),
        "condition": details.get("condition") or details.get("description")
    }
    return weather_details


def normalize_leaf_severities(
    sev_a: float,
    conf_a: float,
    sev_b: float,
    conf_b: float
):
    if sev_a < DISEASE_DETECTION_THRESHOLD and sev_b < DISEASE_DETECTION_THRESHOLD:
        return 0.0, 0.0, 0.0, 0.0

    if sev_a >= DISEASE_DETECTION_THRESHOLD and sev_b < DISEASE_DETECTION_THRESHOLD:
        return sev_a, conf_a, 0.0, 0.0

    if sev_b >= DISEASE_DETECTION_THRESHOLD and sev_a < DISEASE_DETECTION_THRESHOLD:
        return 0.0, 0.0, sev_b, conf_b

    if sev_a >= CO_INFECTION_THRESHOLD and sev_b >= CO_INFECTION_THRESHOLD:
        return sev_a, conf_a, sev_b, conf_b

    if sev_a >= sev_b * DOMINANCE_RATIO:
        return sev_a, conf_a, 0.0, 0.0

    if sev_b >= sev_a * DOMINANCE_RATIO:
        return 0.0, 0.0, sev_b, conf_b

    return sev_a, conf_a, sev_b, conf_b

async def process_upload(
    file: UploadFile,
    session_id: str,
    day: int,
    lat: float,
    lon: float
):
    image_bytes = await file.read()

    # Step 1: Weather (Live API)
    weather = get_weather_risk(lat, lon)
    weather_details = build_weather_details(weather)

    # Step 2: Gate check (Accept/Reject)
    valid, confidence, reason = is_valid_leaf(image_bytes)
    if not valid:
        return {
            "session_id":           session_id,
            "day":                  day,
            "image_valid":          False,
            "rejection_reason":     reason,
            "disease_a_severity":   0.0,
            "disease_b_severity":   0.0,
            "disease_a_confidence": 0.0,
            "disease_b_confidence": 0.0,
            "combined_risk_score":  0.0,
            "combined_risk_level":  "UNKNOWN",
            "weather_risk_score":   None,
            "weather_risk_level":   None,
            "weather_alert":        None,
            "weather_details":      weather_details,
            "daily_status":         None,
            "daily_alerts":         [],
            "treatment_advice":     None
        }

    # Step 3: U-Net Inference
    (sev_a, conf_a), (sev_b, conf_b) = await asyncio.gather(
        run_in_threadpool(get_leaf_severity, image_bytes, "A"),
        run_in_threadpool(get_leaf_severity, image_bytes, "B"),
    )
    sev_a, conf_a, sev_b, conf_b = normalize_leaf_severities(
        sev_a, conf_a, sev_b, conf_b
    )

    # Step 4: Load Previous History from DB
    history = get_session_history(session_id)
    prev_sev_a = history.get("day1", {}).get("sev_a") if day == 3 else None
    prev_sev_b = history.get("day1", {}).get("sev_b") if day == 3 else None

    # Step 5: Rule Engine (Combined Risk)
    daily = compute_daily_output(
        day       = day,
        severity_a= sev_a,
        severity_b= sev_b,
        weather   = weather,
        prev_severity_a = prev_sev_a,
        prev_severity_b = prev_sev_b
    )

    # Step 6: RAG-based Daily Treatment Advice
    treatment_advice = None
    if sev_a > 5 or sev_b > 5:
        dom_disease = "Early_Blight" if sev_a >= sev_b else "Late_Blight"
        treatment_advice = get_alternative_treatment(
            failed_medicine="None",
            failed_class="None",
            disease_name=dom_disease,
            weather=weather
        )

    # Step 7: Persist to SQLite Database
    save_daily_data(
        session_id, day, sev_a, sev_b, weather, 
        daily["combined_risk_score"], daily["combined_risk_level"], 
        treatment_advice
    )

    return {
        "session_id":           session_id,
        "day":                  day,
        "image_valid":          True,
        "rejection_reason":     None,
        "disease_a_severity":   round(sev_a, 2),
        "disease_b_severity":   round(sev_b, 2),
        "disease_a_confidence": round(conf_a, 4),
        "disease_b_confidence": round(conf_b, 4),
        "combined_risk_score":  daily["combined_risk_score"],
        "combined_risk_level":  daily["combined_risk_level"],
        "weather_risk_score":   weather["risk_score"],
        "weather_risk_level":   weather["risk_level"],
        "weather_alert":        weather["alert"],
        "weather_details":      weather_details,
        "daily_status":         daily["status"],
        "daily_alerts":         daily["alerts"],
        "treatment_advice":     treatment_advice
    }


async def compute_trr_result(session_id: str):
    # Load from DB
    data = get_session_history(session_id)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    if "day1" not in data:
        raise HTTPException(status_code=400, detail="Missing Day 1 upload.")

    if "day7" not in data:
        uploaded_days = get_all_uploaded_days(session_id)
        days_str = ", ".join([f"Day {d}" for d in uploaded_days])
        raise HTTPException(
            status_code=400, 
            detail=f"Missing Day 7 upload. Uploaded: {days_str}"
        )

    d1 = data["day1"]
    d7 = data["day7"]
    weather_history = [v.get("weather", {}) for v in data.values()]

    result = compute_trr(
        day1_sev_a      = d1["sev_a"],
        day7_sev_a      = d7["sev_a"],
        day1_sev_b      = d1["sev_b"],
        day7_sev_b      = d7["sev_b"],
        weather_history = weather_history
    )

    result["session_id"] = session_id
    return result
