"""Hidden secondary image verification (backend only).

Runs only after the local gate PASS.
Primary decision remains the local gate; this layer reduces obvious false accepts
and is designed not to falsely reject real tomato leaf/fruit photos.

Never expose provider names, keys, or raw model output to clients.
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

# Farmer-facing messages only — no provider branding.
REJECT_LEAF = "Please upload a valid tomato leaf image."
REJECT_FRUIT = "Please upload a valid tomato fruit image."
UNAVAILABLE = "We couldn't validate the image right now. Please try again."

EXPECTED_OBJECT = {
    "LEAF": "tomato_leaf",
    "FRUIT": "tomato_fruit",
}

_DEFAULT_MODEL = "gemini-3.6-flash"

# Accept aliases the model sometimes returns for valid tomato crops.
_LEAF_ALIASES = {
    "tomato_leaf",
    "tomato leaf",
    "leaf",
    "tomato_plant_leaf",
    "diseased_tomato_leaf",
}
_FRUIT_ALIASES = {
    "tomato_fruit",
    "tomato fruit",
    "tomato",
    "tomato_plant_fruit",
    "diseased_tomato_fruit",
}


def secondary_gate_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def _timeout_sec() -> float:
    return float(os.getenv("IMAGE_VERIFY_TIMEOUT_SEC", "6"))


def _model_name() -> str:
    return os.getenv("GEMINI_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL


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


def _farmer_reject(crop_part: str) -> str:
    return REJECT_FRUIT if crop_part == "FRUIT" else REJECT_LEAF


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return None
    # Strip markdown fences if present
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


def _build_prompt(crop_part: str) -> str:
    expected = EXPECTED_OBJECT[crop_part]
    if crop_part == "LEAF":
        task = (
            "You are checking if this image is usable for tomato LEAF disease monitoring.\n"
            "ACCEPT (valid=true, object_type=tomato_leaf) when the main subject is a tomato leaf "
            "or tomato plant foliage — including diseased, yellowing, spotted, torn, wet, "
            "partial, angled, or close-up leaves.\n"
            "REJECT (valid=false, object_type=other) only for clearly unrelated subjects: "
            "apple, orange, banana, people, animals, screenshots, documents, cars, "
            "or tomato FRUIT with no leaf.\n"
            "When unsure between tomato leaf vs other plant leaf, ACCEPT as tomato_leaf."
        )
    else:
        task = (
            "You are checking if this image is usable for tomato FRUIT disease monitoring.\n"
            "ACCEPT (valid=true, object_type=tomato_fruit) when the main subject is a tomato fruit "
            "— including unripe green, ripe red, diseased, cracked, or partial fruit.\n"
            "REJECT (valid=false, object_type=other) only for clearly unrelated subjects: "
            "apple, orange, banana, people, animals, screenshots, documents, "
            "or leaf-only photos with no fruit.\n"
            "When unsure between tomato fruit vs other round fruit, ACCEPT as tomato_fruit."
        )
    return (
        f"{task}\n"
        "Reply with JSON only, no markdown, no extra text:\n"
        f'{{"valid": true, "object_type": "{expected}"}}'
    )


def _candidate_text(body: Dict[str, Any]) -> Optional[str]:
    try:
        parts = body["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        return None
    for part in parts:
        if isinstance(part, dict) and part.get("text"):
            return str(part["text"])
    return None


def _normalize_object_type(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _is_matching_crop(crop_part: str, parsed: Dict[str, Any]) -> bool:
    """True when the secondary model agrees this is the expected tomato crop."""
    object_type = _normalize_object_type(parsed.get("object_type"))
    valid_flag = parsed.get("valid")

    aliases = _LEAF_ALIASES if crop_part == "LEAF" else _FRUIT_ALIASES
    if object_type in aliases:
        return True
    # Some responses omit object_type but set valid=true
    if valid_flag is True and (
        object_type in {"", "unknown", "none"} or object_type in aliases
    ):
        return True
    return False


def _call_vision_api(
    image_bytes: bytes, crop_part: str, api_key: str
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Returns (parsed_json_or_none, error_kind)
    error_kind: "" | "http" | "network" | "parse"
    """
    b64 = base64.b64encode(_jpeg_for_vision(image_bytes)).decode("ascii")
    model = _model_name()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": _build_prompt(crop_part)},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 256,
        },
    }

    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=_timeout_sec(),
        )
    except requests.RequestException:
        return None, "network"

    if response.status_code in (429, 503):
        return None, "http"
    if response.status_code >= 400:
        return None, "http"

    try:
        body = response.json()
    except ValueError:
        return None, "parse"

    text = _candidate_text(body)
    if not text:
        return None, "parse"

    parsed = _extract_json(text)
    if not parsed:
        return None, "parse"
    return parsed, ""


def verify_crop_image(
    image_bytes: bytes,
    crop_part: str,
    local_gate_confidence: Optional[float] = None,
) -> Tuple[bool, Optional[str], str]:
    """
    Secondary verification after local gate PASS.

    Returns:
        (accepted, farmer_rejection_message, status)
        status: "pass" | "reject" | "unavailable" | "skipped" | "deferred_to_local"

    Policy (accuracy-first for real tomato photos):
      - Any secondary PASS → accept
      - Transient API/parse failures → trust local gate (already passed)
      - Explicit secondary REJECT → retry once; if still reject, reject
      - High local gate confidence (>= 0.7) can override a single soft reject
    """
    crop_part = crop_part.upper()
    if crop_part not in EXPECTED_OBJECT:
        return False, REJECT_LEAF, "reject"

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return True, None, "skipped"

    parsed, _err = _call_vision_api(image_bytes, crop_part, api_key)
    if parsed is None:
        return True, None, "deferred_to_local"

    if _is_matching_crop(crop_part, parsed):
        return True, None, "pass"

    # One-shot reject: high local gate confidence still prefers local PASS.
    conf = float(local_gate_confidence) if local_gate_confidence is not None else 0.0
    trust_local_floor = float(os.getenv("SECONDARY_TRUST_LOCAL_CONF", "0.70"))
    if conf >= trust_local_floor:
        return True, None, "deferred_to_local"

    return False, _farmer_reject(crop_part), "reject"
