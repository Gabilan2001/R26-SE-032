"""Farmer-facing monitoring insight — explanation layer only.

Takes structured monitoring numbers already computed by the backend and
returns plain-language text. Never invents severity percentages or trends.
Never exposes model/provider names to clients.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import requests

_DEFAULT_MODEL = "gemini-3.6-flash"


def _timeout_sec() -> float:
    return float(os.getenv("GEMINI_TIMEOUT_SEC", "45"))


def _model_name() -> str:
    return os.getenv("GEMINI_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL


def _api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def build_insight_payload(
    *,
    crop_part: str,
    overall_status: str,
    monitoring_summary: Optional[Dict[str, Any]],
    observations_summary: List[Dict[str, Any]],
    latest_recommendation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Structured facts only — no fabricated values."""
    summary = monitoring_summary or {}
    timeline = []
    for i, obs in enumerate(observations_summary):
        score = obs.get("severity_score")
        pct = None
        if score is not None:
            try:
                pct = round(float(score) * 100.0, 1)
            except (TypeError, ValueError):
                pct = None
        timeline.append(
            {
                "observation": i + 1,
                "severity_pct": pct,
                "severity_class": obs.get("severity_class"),
                "trend": obs.get("trend"),
                "consistency": obs.get("consistency_status"),
            }
        )

    return {
        "crop_part": crop_part,
        "overall_status": overall_status,
        "initial_severity_pct": summary.get("initial_severity_pct"),
        "peak_severity_pct": summary.get("peak_severity_pct"),
        "final_severity_pct": summary.get("final_severity_pct"),
        "overall_change_pct": summary.get("overall_change_pct"),
        "overall_trend": summary.get("overall_trend") or overall_status,
        "severity_timeline": summary.get("severity_timeline"),
        "peak_observation_number": summary.get("peak_observation_number"),
        "observation_count": summary.get("observation_count")
        or len(observations_summary),
        "observations": timeline,
        "has_worsening_guidance": bool(latest_recommendation),
    }


def _template_insight(payload: Dict[str, Any]) -> str:
    """Short farmer-friendly fallback when the language API is unavailable."""
    crop = "leaf" if str(payload.get("crop_part", "")).upper() == "LEAF" else "fruit"
    trend = str(payload.get("overall_trend") or payload.get("overall_status") or "STABLE")
    initial = payload.get("initial_severity_pct")
    final = payload.get("final_severity_pct")
    change = payload.get("overall_change_pct")
    count = int(payload.get("observation_count") or 0)

    trend_text = {
        "IMPROVING": "getting better",
        "WORSENING": "getting worse",
        "STABLE": "about the same",
        "RECOVERED": "looking recovered",
        "BASELINE": "just starting",
    }.get(trend, trend.lower())

    line1 = f"From your {count} tomato {crop} photo(s), the plant looks {trend_text}."

    if initial is not None and final is not None:
        change_bit = ""
        if change is not None:
            try:
                change_bit = f" ({float(change):+.1f}%)"
            except (TypeError, ValueError):
                change_bit = ""
        line2 = (
            f"Estimated severity: {float(initial):g}% → {float(final):g}%{change_bit}. "
            "Keep uploading on planned days."
        )
    else:
        line2 = "Keep uploading on planned days."

    return f"{line1} {line2}"


def _call_language_api(payload: Dict[str, Any]) -> Optional[str]:
    key = _api_key()
    if not key:
        return None

    prompt = (
        "Write a VERY short tomato monitoring note for a farmer in Sri Lanka.\n"
        "Rules:\n"
        "- Use ONLY the numbers in the JSON. Do not invent percentages or treatments.\n"
        "- Exactly 2 short sentences. Simple words. No jargon.\n"
        "- Sentence 1: overall condition (better / worse / about the same).\n"
        "- Sentence 2: start % → latest %, then say keep checking on planned days.\n"
        "- Do not mention AI, models, APIs, brand names, treatment, or diagnosis.\n"
        "- Do not list peak observation, timeline arrows, or disclaimers.\n\n"
        f"JSON:\n{json.dumps(payload, ensure_ascii=True)}"
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{_model_name()}:generateContent"
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 120},
    }
    try:
        response = requests.post(
            url, params={"key": key}, json=body, timeout=_timeout_sec()
        )
    except requests.RequestException:
        return None

    if response.status_code >= 400:
        return None
    try:
        parts = response.json()["candidates"][0]["content"].get("parts") or []
        text = next(
            (p.get("text") for p in parts if isinstance(p, dict) and p.get("text")),
            None,
        )
    except (KeyError, IndexError, TypeError, ValueError):
        return None

    if not text:
        return None
    cleaned = re.sub(r"^```(?:\w+)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    # Cap length if the model ignores the short-text rule
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    if len(sentences) > 2:
        cleaned = " ".join(sentences[:2])
    for banned in ("gemini", "google", "openai", "chatgpt", "claude", "llm", "api key"):
        if banned in cleaned.lower():
            return None
    return cleaned


def generate_farmer_insight(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns farmer-facing insight dict.
    `source` is internal only — frontend should not display it as branding.
    """
    text = _call_language_api(payload)
    if text:
        return {
            "available": True,
            "title": "Monitoring insight",
            "text": text,
            "disclaimer": None,
            "source": "language_api",
        }

    return {
        "available": True,
        "title": "Monitoring insight",
        "text": _template_insight(payload),
        "disclaimer": None,
        "source": "template",
    }
