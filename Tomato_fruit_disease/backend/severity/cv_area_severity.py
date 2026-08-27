"""
Classical OpenCV estimator of visually affected area on tomato leaf / fruit.

No ML training. Produces an *estimated* affected-area percentage:
  estimated_affected_area_percentage = affected_pixels / subject_pixels * 100

Classification (project requirement):
  0–30% → LOW
  >30%  → HIGH

This is a visual estimate, not expert/medical disease quantification.
"""

from __future__ import annotations

import io
from typing import Dict, Tuple

import cv2
import numpy as np
from PIL import Image

from config.observation_config import SEVERITY_AREA_THRESHOLD


def _decode(image_bytes: bytes, max_side: int = 512) -> np.ndarray:
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    rgb = np.array(pil)
    h, w = rgb.shape[:2]
    scale = max_side / float(max(h, w))
    if scale < 1.0:
        rgb = cv2.resize(
            rgb,
            (max(64, int(w * scale)), max(64, int(h * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return rgb


def _leaf_subject_mask(hsv: np.ndarray) -> np.ndarray:
    """Isolate leaf-like vegetation (exclude pale background)."""
    h, s, v = cv2.split(hsv)
    green = ((h >= 20) & (h <= 100) & (s >= 25) & (v >= 20) & (v <= 245)).astype(np.uint8)
    # Include chlorotic / diseased leaf tissue that is still plant-like
    chlorotic = ((h >= 10) & (h <= 40) & (s >= 20) & (v >= 30) & (v <= 240)).astype(np.uint8)
    brownish = ((h <= 25) | (h >= 160)) & (s >= 20) & (s <= 200) & (v >= 20) & (v <= 180)
    mask = np.clip(green + chlorotic + brownish.astype(np.uint8), 0, 1).astype(np.uint8)
    return _clean_mask(mask)


def _fruit_subject_mask(hsv: np.ndarray) -> np.ndarray:
    """Isolate tomato fruit region (ripe red + unripe green + intermediate)."""
    h, s, v = cv2.split(hsv)
    red = (((h <= 12) | (h >= 165)) & (s >= 40) & (v >= 35)).astype(np.uint8)
    green = ((h >= 28) & (h <= 90) & (s >= 30) & (v >= 30)).astype(np.uint8)
    ripening = ((h >= 5) & (h <= 28) & (s >= 45) & (v >= 40)).astype(np.uint8)
    mask = np.clip(red + green + ripening, 0, 1).astype(np.uint8)
    mask = _clean_mask(mask)
    # Prefer largest blob (main fruit)
    return _keep_largest(mask)


def _clean_mask(mask: np.ndarray) -> np.ndarray:
    u8 = (mask > 0).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    u8 = cv2.morphologyEx(u8, cv2.MORPH_OPEN, k)
    u8 = cv2.morphologyEx(u8, cv2.MORPH_CLOSE, k)
    return (u8 > 0).astype(np.uint8)


def _keep_largest(mask: np.ndarray) -> np.ndarray:
    u8 = (mask > 0).astype(np.uint8) * 255
    n, labels, stats, _ = cv2.connectedComponentsWithStats(u8, connectivity=8)
    if n <= 1:
        return mask
    # skip background label 0
    areas = stats[1:, cv2.CC_STAT_AREA]
    best = 1 + int(np.argmax(areas))
    return (labels == best).astype(np.uint8)


def _adaptive_disease_mask_leaf(
    bgr: np.ndarray, hsv: np.ndarray, subject: np.ndarray
) -> np.ndarray:
    """
    Multi-signal lesion mask inside leaf subject.
    Uses leaf-local statistics so lighting shifts do not hard-code one HSV band.
    """
    if int(subject.sum()) < 80:
        return np.zeros(subject.shape, dtype=np.uint8)

    h, s, v = cv2.split(hsv)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    sub = subject > 0

    v_med = float(np.median(v[sub]))
    s_med = float(np.median(s[sub]))
    h_med = float(np.median(h[sub]))

    # 1) Necrotic / brown / dark relative to leaf median
    dark = sub & (v < max(35.0, v_med * 0.72)) & (v < v_med - 18)
    brown = sub & (((h <= 22) | (h >= 155)) & (s >= 25) & (v <= min(170.0, v_med + 10)))

    # 2) Chlorosis: yellower / less green than leaf median hue, not pure highlight
    yellow = sub & (h >= 12) & (h <= 40) & (s >= 35) & (v >= 45) & (v <= 230)
    # Only keep yellow that differs from healthy green core
    yellow = yellow & ((h < h_med - 8) | (h > h_med + 12) | (s > s_med + 15))

    # 3) Local contrast blobs (lesion texture) via adaptive threshold on gray
    local = gray.copy()
    local[~sub] = int(np.median(gray[sub]))
    blur = cv2.GaussianBlur(local, (15, 15), 0)
    diff = cv2.absdiff(local, blur)
    tex = sub & (diff > max(12, int(0.12 * v_med)))

    # 4) Exclude specular highlights / pale background bleed
    highlight = sub & (v > 230) & (s < 40)

    disease = (dark | brown | yellow | tex) & (~highlight)
    disease_u8 = disease.astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    disease_u8 = cv2.morphologyEx(disease_u8, cv2.MORPH_OPEN, k)
    disease_u8 = cv2.morphologyEx(disease_u8, cv2.MORPH_CLOSE, k)
    return disease_u8


def _adaptive_disease_mask_fruit(
    bgr: np.ndarray, hsv: np.ndarray, subject: np.ndarray
) -> np.ndarray:
    """
    Multi-signal lesion mask inside fruit subject.
    Avoids counting normal ripe red / healthy green as disease.
    """
    if int(subject.sum()) < 80:
        return np.zeros(subject.shape, dtype=np.uint8)

    h, s, v = cv2.split(hsv)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    sub = subject > 0

    v_med = float(np.median(v[sub]))
    s_med = float(np.median(s[sub]))

    # Dark / sunken lesions relative to fruit body
    dark = sub & (v < max(30.0, v_med * 0.68)) & (v < v_med - 22)

    # Brown / black rot tones (not bright ripe red)
    brown = sub & (((h <= 20) | (h >= 160)) & (s >= 25) & (v <= min(140.0, v_med - 5)))

    # Atypical pale/yellow soft spots on green or red fruit
    pale = sub & (v > v_med + 25) & (s < max(40.0, s_med - 10)) & (v < 245)

    # Local contrast (lesion edges)
    local = gray.copy()
    local[~sub] = int(np.median(gray[sub]))
    blur = cv2.GaussianBlur(local, (17, 17), 0)
    diff = cv2.absdiff(local, blur)
    tex = sub & (diff > max(14, int(0.14 * v_med)))

    # Exclude healthy ripe red body (high S, mid-high V, red hue) unless also dark/tex
    healthy_red = sub & (((h <= 10) | (h >= 170)) & (s >= max(60.0, s_med * 0.7)) & (v >= v_med - 8))
    healthy_green = sub & ((h >= 35) & (h <= 85) & (s >= 35) & (np.abs(v.astype(np.float32) - v_med) < 18))

    disease = (dark | brown | pale | tex) & (~(healthy_red & ~dark & ~tex)) & (~(healthy_green & ~dark & ~tex))
    # Soften: require disease not equal to entire healthy skin
    disease_u8 = disease.astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    disease_u8 = cv2.morphologyEx(disease_u8, cv2.MORPH_OPEN, k)
    disease_u8 = cv2.morphologyEx(disease_u8, cv2.MORPH_CLOSE, k)
    return disease_u8


def estimate_affected_area(image_bytes: bytes, crop_part: str) -> Dict:
    """
    Returns dict with:
      estimated_affected_area_percentage (0–100)
      severity_score (0–1) = percentage / 100
      severity_class LOW|HIGH using SEVERITY_AREA_THRESHOLD (default 0.30)
      subject_pixels, affected_pixels
    """
    crop = (crop_part or "").strip().upper()
    rgb = _decode(image_bytes)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    if crop == "FRUIT":
        subject = _fruit_subject_mask(hsv)
        disease = _adaptive_disease_mask_fruit(bgr, hsv, subject)
    else:
        subject = _leaf_subject_mask(hsv)
        disease = _adaptive_disease_mask_leaf(bgr, hsv, subject)

    # Disease only inside subject
    disease = ((disease > 0) & (subject > 0)).astype(np.uint8)

    subject_pixels = int(subject.sum())
    affected_pixels = int(disease.sum())

    if subject_pixels < 50:
        # Fallback: weak subject — avoid 100% false HIGH; treat as low evidence
        percentage = 0.0
    else:
        percentage = 100.0 * float(affected_pixels) / float(subject_pixels)

    percentage = float(np.clip(percentage, 0.0, 100.0))
    score = percentage / 100.0
    severity_class = "HIGH" if score > SEVERITY_AREA_THRESHOLD else "LOW"

    return {
        "estimated_affected_area_percentage": round(percentage, 1),
        "severity_score": round(score, 4),
        "severity_class": severity_class,
        "subject_pixels": subject_pixels,
        "affected_pixels": affected_pixels,
        "severity_area_threshold": SEVERITY_AREA_THRESHOLD,
        "crop_part": crop if crop in {"LEAF", "FRUIT"} else "LEAF",
    }


def classify_from_percentage(percentage: float) -> Tuple[float, str]:
    """Helper: percentage → (severity_score, severity_class)."""
    pct = float(np.clip(percentage, 0.0, 100.0))
    score = pct / 100.0
    cls = "HIGH" if score > SEVERITY_AREA_THRESHOLD else "LOW"
    return round(score, 4), cls
