"""Backend-only secondary visual severity verification.

Runs AFTER primary OpenCV + calibrated/current threshold LOW/HIGH.
Never overwrites primary severity. Never exposed to farmer UI.

Does not replace ml.predict.secondary_image_verify (image gate).
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
from typing import Any, Dict, Optional, Tuple

import requests
from PIL import Image

_DEFAULT_MODEL = "gemini-3.6-flash"
STATUS_CONSISTENT = "CONSISTENT"
STATUS_INCONSISTENT = "INCONSISTENT"
STATUS_UNAVAILABLE = "SECONDARY_UNAVAILABLE"


def _jpeg_for_vision(image_bytes: bytes, max_side: int = 640) -> bytes:
    try:
        im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = im.size
        scale = max_side / float(max(w, h, 1))
        if scale < 1.0:
            im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=72)
        return buf.getvalue()
    except Exception:
        return image_bytes


def _timeout_sec() -> float:
    return float(os.getenv("SECONDARY_SEVERITY_TIMEOUT_SEC", "5"))


def _model_name() -> str:
    return os.getenv("GEMINI_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL


def _api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def compare_primary_to_secondary(
    primary_severity: str, secondary_severity: Optional[str], *, available: bool
) -> str:
    if not available or not secondary_severity:
        return STATUS_UNAVAILABLE
    if str(secondary_severity).strip().upper() == str(primary_severity).strip().upper():
        return STATUS_CONSISTENT
    return STATUS_INCONSISTENT


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return None
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _normalize_payload(parsed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sev = str(parsed.get("severity") or "").strip().upper()
    if sev not in {"LOW", "HIGH"}:
        return None
    conf = parsed.get("confidence")
    try:
        confidence = float(conf) if conf is not None else None
    except (TypeError, ValueError):
        confidence = None
    area = parsed.get("estimated_affected_area_percentage")
    try:
        area_pct = float(area) if area is not None else None
    except (TypeError, ValueError):
        area_pct = None
    reasoning = parsed.get("reasoning")
    return {
        "secondary_severity": sev,
        "secondary_confidence": confidence,
        "secondary_estimated_area_percentage": area_pct,
        "secondary_reasoning": str(reasoning).strip() if reasoning else None,
    }


def _unavailable(primary_severity: str) -> Dict[str, Any]:
    cls = str(primary_severity).strip().upper() or "LOW"
    return {
        "verification_status": STATUS_UNAVAILABLE,
        "final_severity": cls,
        "secondary_severity": None,
        "secondary_confidence": None,
        "secondary_estimated_area_percentage": None,
        "secondary_reasoning": None,
    }


def _build_prompt(crop_part: str) -> str:
    part = "leaf" if str(crop_part).upper() == "LEAF" else "fruit"
    return (
        f"Inspect this tomato {part} photo for visible disease-affected area.\n"
        "This is a SECONDARY verification only, not the primary measurement "
        "and not expert or clinical ground truth.\n"
        "Do not give treatment, medicine, or diagnosis advice.\n"
        "Reply with JSON only, no markdown, no extra text:\n"
        '{"estimated_affected_area_percentage": 0.0, "severity": "LOW", '
        '"confidence": 0.0, "reasoning": "short visual note"}'
    )


def _candidate_text(body: Dict[str, Any]) -> Optional[str]:
    try:
        parts = body["candidates"][0]["content"].get("parts") or []
        return next(
            (p.get("text") for p in parts if isinstance(p, dict) and p.get("text")),
            None,
        )
    except (KeyError, IndexError, TypeError):
        return None


def _call_vision_api(image_bytes: bytes, crop_part: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    key = _api_key()
    if not key:
        return None, False
    b64 = base64.b64encode(_jpeg_for_vision(image_bytes)).decode("ascii")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{_model_name()}:generateContent"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": _build_prompt(crop_part)},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 160},
    }
    try:
        response = requests.post(
            url, params={"key": key}, json=payload, timeout=_timeout_sec()
        )
    except requests.RequestException:
        return None, False
    if response.status_code >= 400:
        return None, False
    try:
        body = response.json()
    except ValueError:
        return None, False
    text = _candidate_text(body)
    parsed = _extract_json(text or "")
    if not parsed:
        return None, False
    return parsed, True


def verify_secondary_severity(
    image_bytes: bytes,
    crop_part: str,
    primary_severity: str,
) -> Dict[str, Any]:
    """One verification attempt. Never raises. Never changes primary class."""
    primary = str(primary_severity).strip().upper() or "LOW"
    parsed, ok = _call_vision_api(image_bytes, crop_part)
    if not ok or not parsed:
        return _unavailable(primary)
    normalized = _normalize_payload(parsed)
    if not normalized:
        return _unavailable(primary)
    status = compare_primary_to_secondary(
        primary, normalized["secondary_severity"], available=True
    )
    return {
        "verification_status": status,
        "final_severity": primary,
        **normalized,
    }
