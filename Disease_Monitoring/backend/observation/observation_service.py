"""Orchestrates the observation-based monitoring pipeline."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, UploadFile

from config.observation_config import (
    CROP_PARTS,
    DISEASES_BY_CROP,
)
from consistency.consistency_checker import check_consistency
from consistency.similarity import cosine_similarity
from ml.predict.gate_predictor import is_valid_fruit, is_valid_leaf
from ml.predict.secondary_image_verify import verify_crop_image
from observation.observation_repository import (
    create_case,
    get_all_observations,
    get_case,
    get_last_accepted_observation,
    insert_observation,
    public_observation,
    save_observation_image,
)
from observation.recommendation_service import get_worsening_recommendation
from observation.trend_analysis import (
    compute_monitoring_summary,
    compute_overall_status,
    compute_trend,
)
from observation.weather_context import fetch_weather_context
from utils.location_service import resolve_manual_location, resolve_observation_location
from utils.secondary_severity_verify import verify_secondary_severity
from severity.fruit.fruit_severity import (
    FruitModelNotConfiguredError,
    predict_fruit_severity,
)
from severity.leaf.efficientnet_severity import (
    ModelNotConfiguredError,
    predict_leaf_severity,
)


def _validate_crop_part(crop_part: str) -> str:
    normalized = crop_part.strip().upper()
    if normalized not in CROP_PARTS:
        raise HTTPException(400, f"crop_part must be one of {sorted(CROP_PARTS)}")
    return normalized


def _validate_disease(crop_part: str, disease: str) -> str:
    normalized = disease.strip().lower()
    allowed = DISEASES_BY_CROP.get(crop_part, set())
    if normalized not in allowed:
        raise HTTPException(
            400,
            f"disease '{disease}' is not supported for crop_part {crop_part}. "
            f"Allowed: {sorted(allowed)}",
        )
    return normalized


def _run_gate(crop_part: str, image_bytes: bytes):
    if crop_part == "LEAF":
        return is_valid_leaf(image_bytes)
    return is_valid_fruit(image_bytes)


def _run_severity(crop_part: str, image_bytes: bytes) -> Dict[str, Any]:
    try:
        if crop_part == "LEAF":
            return predict_leaf_severity(image_bytes)
        return predict_fruit_severity(image_bytes)
    except (ModelNotConfiguredError, FruitModelNotConfiguredError) as exc:
        raise HTTPException(503, str(exc)) from exc


async def create_monitoring_case(crop_part: str, label: Optional[str] = None) -> Dict[str, Any]:
    crop_part = _validate_crop_part(crop_part)
    return create_case(crop_part, label)


async def get_monitoring_case(case_id: str) -> Dict[str, Any]:
    case = get_case(case_id)
    if not case:
        raise HTTPException(404, f"Case '{case_id}' not found.")
    return case


async def process_observation_upload(
    case_id: str,
    file: UploadFile,
    crop_part: str,
    disease: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    area: Optional[str] = None,
    district: Optional[str] = None,
    province: Optional[str] = None,
    location_label: Optional[str] = None,
    location_source: Optional[str] = None,
    confirm_same_case: bool = False,
) -> Dict[str, Any]:
    case = get_case(case_id)
    if not case:
        raise HTTPException(404, f"Case '{case_id}' not found.")

    crop_part = _validate_crop_part(crop_part)
    if case["crop_part"] != crop_part:
        raise HTTPException(
            400,
            f"Case '{case_id}' is registered for {case['crop_part']}, not {crop_part}.",
        )

    disease = _validate_disease(crop_part, disease)
    image_bytes = await file.read()

    valid, gate_confidence, rejection_reason = _run_gate(crop_part, image_bytes)
    if not valid:
        return {
            "accepted": False,
            "case_id": case_id,
            "crop_part": crop_part,
            "image_valid": False,
            "gate_confidence": gate_confidence,
            "rejection_reason": rejection_reason,
        }

    # Hidden secondary check (backend only). UI sees one validation result.
    secondary_ok, secondary_reason, secondary_status = verify_crop_image(
        image_bytes,
        crop_part,
        local_gate_confidence=gate_confidence,
    )
    if not secondary_ok:
        return {
            "accepted": False,
            "case_id": case_id,
            "crop_part": crop_part,
            "image_valid": False,
            "gate_confidence": gate_confidence,
            "rejection_reason": secondary_reason
            or (
                "We couldn't validate the image right now. Please try again."
                if secondary_status == "unavailable"
                else rejection_reason
            ),
        }

    severity_result = _run_severity(crop_part, image_bytes)
    embedding = severity_result["embedding"]

    previous = get_last_accepted_observation(case_id, crop_part)
    similarity_score = None
    if previous:
        if previous["crop_part"] != crop_part:
            raise HTTPException(500, "Internal error: crop_part mismatch in observation history.")
        similarity_score = round(cosine_similarity(embedding, previous["embedding"]), 4)

    consistency_status, accepted, consistency_reason = check_consistency(
        similarity_score,
        is_first_observation=previous is None,
        confirm_same_case=confirm_same_case,
    )

    if not accepted:
        return {
            "accepted": False,
            "case_id": case_id,
            "crop_part": crop_part,
            "image_valid": True,
            "gate_confidence": gate_confidence,
            "similarity_score": similarity_score,
            "consistency_status": consistency_status,
            "rejection_reason": consistency_reason,
            "disease": disease,
        }

    previous_score = previous["severity_score"] if previous else None
    trend = compute_trend(severity_result["severity_score"], previous_score)

    primary_severity = str(severity_result["severity_class"]).upper()
    secondary_verify = verify_secondary_severity(
        image_bytes, crop_part, primary_severity
    )
    cnn_high_prob = severity_result.get("cnn_high_prob")
    severity_evidence = {
        "cnn_high_prob": cnn_high_prob,
        **secondary_verify,
    }

    location = resolve_observation_location(
        latitude=latitude,
        longitude=longitude,
        area=area,
        district=district,
        province=province,
        location_label=location_label,
        location_source=location_source,
    )
    weather_lat = location.get("latitude")
    weather_lon = location.get("longitude")
    used_default_weather_location = False
    if weather_lat is None or weather_lon is None:
        # Weather API needs coordinates — fall back to Colombo so snapshots still work.
        default_place = resolve_manual_location("Colombo")
        weather_lat = default_place.get("latitude")
        weather_lon = default_place.get("longitude")
        used_default_weather_location = True
        if not location.get("area"):
            location = {
                **location,
                "latitude": weather_lat,
                "longitude": weather_lon,
                "area": "Colombo (default)",
                "district": default_place.get("district"),
                "province": default_place.get("province"),
                "source": location.get("source") or "default",
            }

    weather_context = fetch_weather_context(weather_lat, weather_lon)
    if used_default_weather_location and weather_context.get("available"):
        weather_context = {
            **weather_context,
            "used_default_location": True,
            "interpretation": (
                "Weather shown for Colombo (default). "
                "Set GPS or pick your farm area on Observation 1 for local weather. "
                + str(weather_context.get("interpretation") or "")
            ),
        }
    recommendation = get_worsening_recommendation(disease, trend, weather_context)

    observation_id = f"OBS-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()
    image_path = save_observation_image(case_id, observation_id, image_bytes)

    record = {
        "observation_id": observation_id,
        "case_id": case_id,
        "crop_part": crop_part,
        "created_at": created_at,
        "disease": disease,
        "severity_score": severity_result["severity_score"],
        "severity_class": primary_severity,
        "embedding": embedding,
        "similarity_score": similarity_score,
        "consistency_status": consistency_status,
        "weather_context": weather_context,
        "trend": trend,
        "status": trend,
        "recommendation": recommendation,
        "accepted": True,
        "image_path": image_path,
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "area": location.get("area"),
        "district": location.get("district"),
        "province": location.get("province"),
        "location_source": location.get("source"),
        "severity_evidence": severity_evidence,
    }
    insert_observation(record)

    response_obs = public_observation(record)
    return {
        "accepted": True,
        "case_id": case_id,
        "crop_part": crop_part,
        "image_valid": True,
        "gate_confidence": gate_confidence,
        "observation": response_obs,
        "overall_status": await get_case_status(case_id),
    }


async def list_observations(case_id: str) -> Dict[str, Any]:
    case = get_case(case_id)
    if not case:
        raise HTTPException(404, f"Case '{case_id}' not found.")
    observations = [public_observation(o) for o in get_all_observations(case_id)]
    return {"case_id": case_id, "crop_part": case["crop_part"], "observations": observations}


async def get_case_status(case_id: str) -> Dict[str, Any]:
    case = get_case(case_id)
    if not case:
        raise HTTPException(404, f"Case '{case_id}' not found.")

    crop_part = case["crop_part"]
    from observation.observation_repository import get_accepted_observations

    accepted = get_accepted_observations(case_id, crop_part)
    public = [public_observation(o) for o in accepted]
    trends = [o["trend"] for o in accepted if o.get("trend")]
    overall = compute_overall_status(trends)
    severity_scores = [float(o["severity_score"]) for o in accepted]
    monitoring_summary = compute_monitoring_summary(severity_scores)

    latest = public[-1] if public else None
    latest_recommendation = latest.get("recommendation") if latest else None

    return {
        "case_id": case_id,
        "crop_part": crop_part,
        "observation_count": len(public),
        "overall_status": overall,
        "monitoring_summary": monitoring_summary,
        "latest_observation": latest,
        "latest_recommendation": latest_recommendation,
        "observations_summary": [
            {
                "observation_id": o["observation_id"],
                "created_at": o["created_at"],
                "severity_score": o["severity_score"],
                "severity_class": o["severity_class"],
                "trend": o.get("trend"),
                "consistency_status": o["consistency_status"],
            }
            for o in public
        ],
    }


async def get_farmer_insight(case_id: str) -> Dict[str, Any]:
    """Explanation-only insight from stored monitoring facts."""
    from utils.monitoring_insight import build_insight_payload, generate_farmer_insight

    status = await get_case_status(case_id)
    if status["observation_count"] == 0:
        return {
            "case_id": case_id,
            "available": False,
            "title": "Monitoring insight",
            "text": "Upload at least one observation to see a monitoring insight.",
            "disclaimer": None,
            "source": "empty",
        }

    payload = build_insight_payload(
        crop_part=status["crop_part"],
        overall_status=status["overall_status"],
        monitoring_summary=status.get("monitoring_summary"),
        observations_summary=status.get("observations_summary") or [],
        latest_recommendation=status.get("latest_recommendation"),
    )
    insight = generate_farmer_insight(payload)
    return {"case_id": case_id, **insight}


async def build_case_report_pdf(case_id: str) -> bytes:
    """PDF report from stored observations + optional insight text."""
    from utils.report_pdf import build_monitoring_report_pdf

    case = get_case(case_id)
    if not case:
        raise HTTPException(404, f"Case '{case_id}' not found.")

    status = await get_case_status(case_id)
    if status["observation_count"] == 0:
        raise HTTPException(400, "No observations available to build a report.")

    observations = [public_observation(o) for o in get_all_observations(case_id)]
    insight = await get_farmer_insight(case_id)
    insight_text = insight.get("text") if insight.get("available") else None

    return build_monitoring_report_pdf(
        case_id=case_id,
        crop_part=case["crop_part"],
        overall_status=status["overall_status"],
        monitoring_summary=status.get("monitoring_summary"),
        observations=observations,
        farmer_insight_text=insight_text,
    )
