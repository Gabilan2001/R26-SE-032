"""Hidden secondary image verification (backend only).

Calls an external vision API after the local gate passes.
Never expose provider names, keys, or raw model output to clients.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from typing import Any, Dict, Optional, Tuple

import requests

# Farmer-facing messages only — no provider branding.
REJECT_LEAF = "Please upload a valid tomato leaf image."
REJECT_FRUIT = "Please upload a valid tomato fruit image."
UNAVAILABLE = "We couldn't validate the image right now. Please try again."

EXPECTED_OBJECT = {
    "LEAF": "tomato_leaf",
    "FRUIT": "tomato_fruit",
}

_DEFAULT_MODEL = "gemini-3.6-flash"


def secondary_gate_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def _timeout_sec() -> float:
    return float(os.getenv("GEMINI_TIMEOUT_SEC", "45"))


def _model_name() -> str:
    return os.getenv("GEMINI_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL


def _farmer_reject(crop_part: str) -> str:
    return REJECT_FRUIT if crop_part == "FRUIT" else REJECT_LEAF


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return None
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
            "Decide if this photo is a suitable close-up of a tomato plant leaf "
            "(may show disease spots). Reject if it is fruit, apple, orange, other crops, "
            "people, screenshots, or unrelated objects."
        )
    else:
        task = (
            "Decide if this photo is a suitable close-up of a tomato fruit "
            "(may show disease). Reject if it is leaf-only, apple, orange, other fruits, "
            "people, screenshots, or unrelated objects."
        )
    return (
        f"{task}\n"
        "Reply with JSON only, no markdown, no extra text:\n"
        f'{{"valid": true or false, "object_type": "{expected}" or "other"}}'
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


def _call_vision_api(image_bytes: bytes, crop_part: str, api_key: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Returns (parsed_json_or_none, error_kind)
    error_kind: "" | "http" | "network" | "parse"
    """
    b64 = base64.b64encode(image_bytes).decode("ascii")
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
) -> Tuple[bool, Optional[str], str]:
    """
    Secondary verification after local gate PASS.

    Returns:
        (accepted, farmer_rejection_message, status)
        status: "pass" | "reject" | "unavailable" | "skipped"
    """
    crop_part = crop_part.upper()
    if crop_part not in EXPECTED_OBJECT:
        return False, REJECT_LEAF, "reject"

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        # Not configured — keep local gate only (dev / CI).
        return True, None, "skipped"

    expected = EXPECTED_OBJECT[crop_part]
    parsed = None
    err = "network"
    for attempt in range(2):
        parsed, err = _call_vision_api(image_bytes, crop_part, api_key)
        if parsed is not None:
            break
        if attempt == 0 and err in {"http", "network"}:
            time.sleep(1.2)
            continue
        break

    if parsed is None:
        return False, UNAVAILABLE, "unavailable"

    valid = parsed.get("valid") is True
    object_type = str(parsed.get("object_type", "")).strip().lower()
    if valid and object_type == expected:
        return True, None, "pass"

    return False, _farmer_reject(crop_part), "reject"
