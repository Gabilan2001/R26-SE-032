import asyncio
import logging

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from ml.predict.gate_predictor import is_valid_fruit
from ml.predict.unet_predictor import get_fruit_multiclass_severity
from utils.weather_utils import get_weather_risk
from services.fruit_rule_engine import compute_fruit_daily_output
from services.rag_engine import get_alternative_treatment
from utils.db_utils import save_fruit_data, get_fruit_history

logger = logging.getLogger(__name__)

def build_weather_details(weather: dict) -> dict:
    details = weather.get("details", {}) if weather else {}
    return {
        "temperature": details.get("temperature"),
        "humidity": details.get("humidity"),
        "wind_speed": details.get("wind_speed"),
        "rainfall": details.get("rainfall_1h", 0.0),
        "condition": details.get("condition") or details.get("description")
    }

async def process_upload(
    file: UploadFile,
    session_id: str,
    day: int,
    lat: float,
    lon: float,
) -> dict:
    image_bytes = await file.read()

    # Step 1 — Gate Check
    valid, gate_conf, reason = is_valid_fruit(image_bytes)
    if not valid:
        return {
            "session_id": session_id,
            "day": day,
            "image_valid": False,
            "rejection_reason": reason,
            "severity": "NONE",
            "confidence": 0.0,
            "dominant_disease": "none",
            "anthracnose_severity": 0.0,
            "blossom_end_rot_severity": 0.0,
            "spotted_wilt_virus_severity": 0.0,
            "healthy_percent": 0.0,
            "combined_risk_score": 0.0,
            "weather_risk_score": 0.0,
            "weather_risk_level": "UNKNOWN",
            "risk_level": "UNKNOWN",
            "weather_alert": None,
            "weather_details": None,
            "daily_status": None,
            "daily_alerts": [],
            "treatment_advice": None
        }

    # Step 2 — UNet Analysis
    unet = await run_in_threadpool(get_fruit_multiclass_severity, image_bytes)
    
    # Step 3 — Weather Data
    weather = get_weather_risk(lat, lon)
    weather_details = build_weather_details(weather)

    # Step 4 — Load History & Rule Engine
    history = get_fruit_history(session_id)
    prev = history.get("day1", {}) if day == 3 else {}
    
    daily = compute_fruit_daily_output(
        day=day,
        sev_anth=unet["anthracnose_severity"],
        sev_ber=unet["blossom_end_rot_severity"],
        sev_swv=unet["spotted_wilt_virus_severity"],
        weather=weather,
        prev_anth=prev.get("sev_anth"),
        prev_ber=prev.get("sev_ber"),
        prev_swv=prev.get("sev_swv")
    )

    # Step 5 — RAG Advice
    treatment_advice = None
    if unet["severity"] != "LOW":
        treatment_advice = get_alternative_treatment(
            failed_medicine="None",
            failed_class="None",
            disease_name=unet["dominant_disease"],
            weather=weather
        )

    # Step 6 — Save to DB
    save_fruit_data(
        session_id, day, 
        unet["anthracnose_severity"], unet["blossom_end_rot_severity"], unet["spotted_wilt_virus_severity"],
        weather, daily["combined_risk_score"], daily["combined_risk_level"],
        treatment_advice
    )

    return {
        "session_id":                  session_id,
        "day":                         day,
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
        "combined_risk_score":         daily["combined_risk_score"],
        "weather_risk_score":          weather["risk_score"],
        "weather_risk_level":          weather["risk_level"],
        "risk_level":                  daily["combined_risk_level"],
        "weather_alert":               weather.get("alert"),
        "weather_details":             weather_details,

        # Monitoring & RAG
        "daily_status":                daily["status"],
        "daily_alerts":                daily["alerts"],
        "treatment_advice":            treatment_advice
    }
