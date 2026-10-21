"""Client-side image quality heuristics (OpenCV) — advisory only, not a gate."""

from __future__ import annotations

import io
from typing import Any, Dict, Literal

import cv2
import numpy as np
from PIL import Image

CheckStatus = Literal["pass", "warn", "fail"]

BLUR_FAIL = 40.0
BLUR_WARN = 90.0
BRIGHT_LOW = 50.0
BRIGHT_HIGH = 210.0
MIN_SIDE_PX = 480
SUBJECT_FILL_WARN = 0.10


def _load_bgr(image_bytes: bytes, max_side: int = 1280) -> tuple[np.ndarray, tuple[int, int]]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        w, h = img.size
    arr = np.array(img)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR), (w, h)


def _blur_score(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _brightness_score(gray: np.ndarray) -> float:
    return float(np.mean(gray))


def _subject_fill_ratio(bgr: np.ndarray) -> float:
    """Rough share of frame occupied by a saturated subject (proxy for distance)."""
    h, w = bgr.shape[:2]
    target_w = 320
    target_h = max(1, int(target_w * h / w))
    small = cv2.resize(bgr, (target_w, target_h))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    mask = ((sat > 30) & (val > 35) & (val < 250)).astype(np.uint8) * 255
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0
    largest = max(cv2.contourArea(c) for c in contours)
    return float(largest / (target_w * target_h))


def _check_item(status: CheckStatus, score: float, message: str, **extra: Any) -> Dict[str, Any]:
    item: Dict[str, Any] = {"status": status, "score": score, "message": message}
    item.update(extra)
    return item


def analyze_image_quality(image_bytes: bytes, crop_part: str = "LEAF") -> Dict[str, Any]:
    """
    Return farmer-friendly quality hints before observation upload.

    Does not reject images — the gate and severity pipeline run on upload as before.
    """
    _ = crop_part  # reserved for future crop-specific tuning

    bgr, (orig_w, orig_h) = _load_bgr(image_bytes)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    blur = _blur_score(gray)
    bright = _brightness_score(gray)
    fill = _subject_fill_ratio(bgr)
    min_side = min(orig_w, orig_h)

    if blur < BLUR_FAIL:
        blur_check = _check_item(
            "fail",
            round(blur, 1),
            "Photo is too blurry. Hold the phone steady and retake.",
        )
    elif blur < BLUR_WARN:
        blur_check = _check_item(
            "warn",
            round(blur, 1),
            "Photo looks slightly blurry. A sharper image helps severity estimates.",
        )
    else:
        blur_check = _check_item("pass", round(blur, 1), "Sharpness looks good.")

    if bright < BRIGHT_LOW:
        bright_check = _check_item(
            "warn",
            round(bright, 1),
            "Photo is too dark. Try better lighting or move to a brighter spot.",
        )
    elif bright > BRIGHT_HIGH:
        bright_check = _check_item(
            "warn",
            round(bright, 1),
            "Photo is very bright. Avoid direct glare on the leaf or fruit.",
        )
    else:
        bright_check = _check_item("pass", round(bright, 1), "Lighting looks good.")

    if min_side < MIN_SIDE_PX:
        dist_check = _check_item(
            "warn",
            round(fill, 3),
            "Move closer so the leaf or fruit fills more of the frame.",
            min_side_px=min_side,
        )
    elif fill < SUBJECT_FILL_WARN:
        dist_check = _check_item(
            "warn",
            round(fill, 3),
            "Subject looks small in the frame. Move closer for a clearer shot.",
            min_side_px=min_side,
        )
    else:
        dist_check = _check_item(
            "pass",
            round(fill, 3),
            "Framing distance looks good.",
            min_side_px=min_side,
        )

    checks = {
        "blur": blur_check,
        "brightness": bright_check,
        "distance": dist_check,
    }
    statuses = [c["status"] for c in checks.values()]

    if "fail" in statuses:
        overall = "poor"
        summary = "Please improve the photo if you can — blur reduces monitoring accuracy."
    elif "warn" in statuses:
        overall = "fair"
        summary = "Photo is usable, but fixing the hints below will improve accuracy."
    else:
        overall = "good"
        summary = "Photo quality looks good for monitoring."

    return {
        "ok": True,
        "checks": checks,
        "overall": overall,
        "farmer_summary": summary,
        "can_upload": True,
    }
