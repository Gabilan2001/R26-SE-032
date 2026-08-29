"""
Deterministic OpenCV pre-gate for tomato leaf / fruit uploads.

No ML training. Multi-signal classical CV:
  sanity → document/screenshot → skin/face → structure →
  texture → color distribution → shape/contour → modality score

crop_part-aware:
  LEAF  → tomato-leaf-like only
  FRUIT → tomato-fruit-like only
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

REJECT_MESSAGE = (
    "Please upload a valid tomato leaf or tomato fruit image."
)
REJECT_MESSAGE_LEAF = (
    "Please upload a valid tomato leaf image."
)
REJECT_MESSAGE_FRUIT = (
    "Please upload a valid tomato fruit image."
)


@dataclass
class PregateResult:
    accepted: bool
    confidence: float
    reason: Optional[str]
    details: Dict[str, float]


def _decode(image_bytes: bytes) -> Optional[np.ndarray]:
    try:
        pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        rgb = np.array(pil)
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            return None
        if min(rgb.shape[0], rgb.shape[1]) < 64:
            return None
        # Cap work size while preserving aspect
        h, w = rgb.shape[:2]
        scale = 512.0 / max(h, w)
        if scale < 1.0:
            rgb = cv2.resize(
                rgb,
                (max(64, int(w * scale)), max(64, int(h * scale))),
                interpolation=cv2.INTER_AREA,
            )
        return rgb
    except Exception:
        return None


def _saturation_value_stats(hsv: np.ndarray) -> Tuple[float, float, float]:
    s = hsv[:, :, 1].astype(np.float32) / 255.0
    v = hsv[:, :, 2].astype(np.float32) / 255.0
    return float(s.mean()), float(v.mean()), float(s.std())


def _document_screenshot_score(rgb: np.ndarray, hsv: np.ndarray, gray: np.ndarray) -> float:
    """High for receipts, PDFs, UI screenshots, text-heavy images."""
    s_mean, v_mean, s_std = _saturation_value_stats(hsv)

    # Near-white / gray background dominance
    white_ratio = float(np.mean((hsv[:, :, 2] > 200) & (hsv[:, :, 1] < 60)))

    # Edge density with strong axis-aligned structure (text/UI)
    edges = cv2.Canny(gray, 80, 160)
    edge_density = float(edges.mean() / 255.0)
    horiz = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    vert = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    axis_ratio = float(
        (np.mean(np.abs(horiz)) + np.mean(np.abs(vert)))
        / (np.mean(np.abs(horiz) + np.abs(vert)) + 1e-6)
    )

    # Local binary-ish contrast typical of printed text
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    local = cv2.absdiff(gray, blur)
    text_like = float(np.mean(local > 18))

    score = 0.0
    score += 0.35 * white_ratio
    score += 0.25 * min(1.0, edge_density / 0.18)
    score += 0.15 * max(0.0, 1.0 - s_mean * 2.5)
    score += 0.15 * text_like
    score += 0.10 * max(0.0, axis_ratio - 0.55) / 0.45
    if s_std < 0.08 and white_ratio > 0.45:
        score += 0.2
    # Unused v_mean kept for lighting awareness in extensions
    _ = v_mean
    return float(np.clip(score, 0.0, 1.0))


def _skin_score(hsv: np.ndarray) -> float:
    """Approximate skin-tone coverage (faces/hands)."""
    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    # OpenCV H: 0-179. Skin often ~0-25 with moderate S/V
    mask = ((h <= 25) | (h >= 160)) & (s >= 30) & (s <= 180) & (v >= 50) & (v <= 240)
    return float(np.mean(mask))


def _structure_score(gray: np.ndarray) -> float:
    """Buildings / vehicles: many long straight edges via Hough."""
    edges = cv2.Canny(gray, 60, 150)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=60, minLineLength=40, maxLineGap=8
    )
    if lines is None:
        return 0.0
    n = len(lines)
    # Normalize: many lines → high structure
    return float(np.clip(n / 80.0, 0.0, 1.0))


def _texture_naturalness(gray: np.ndarray) -> float:
    """
    Organic / photographic texture score.
    Many dataset crops here are 224px and lightly smoothed, so do not
    require high Laplacian variance alone.
    """
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    var = float(lap.var())
    std = float(gray.std())
    edges = cv2.Canny(gray, 50, 120)
    edge_density = float(edges.mean() / 255.0)

    score = 0.0
    if var >= 8:
        score += 0.35 * min(1.0, var / 80.0)
    if std >= 20:
        score += 0.35 * min(1.0, (std - 10.0) / 50.0)
    if edge_density >= 0.01:
        score += 0.30 * min(1.0, edge_density / 0.08)
    return float(np.clip(score, 0.0, 1.0))


def _vegetation_mask(hsv: np.ndarray) -> np.ndarray:
    """Broad green/yellow-green plant mask (not a single RGB rule)."""
    h, s, v = cv2.split(hsv)
    # Multiple green bands + yellow-green chlorosis
    m1 = (h >= 25) & (h <= 95) & (s >= 30) & (v >= 25)
    m2 = (h >= 15) & (h <= 40) & (s >= 40) & (v >= 40)  # yellow-green disease tones
    return (m1 | m2).astype(np.uint8)


def _tomato_fruit_mask(hsv: np.ndarray) -> np.ndarray:
    """
    Tomato fruit colors: ripe red + unripe/green + ripening tones.
    Green band is still tighter than full leaf vegetation.
    """
    h, s, v = cv2.split(hsv)
    red = (((h <= 12) | (h >= 165)) & (s >= 45) & (v >= 35)).astype(np.uint8)
    # Unripe / green tomato (includes BER dark-green fruit body)
    green_fruit = ((h >= 30) & (h <= 85) & (s >= 35) & (v >= 30) & (v <= 220)).astype(
        np.uint8
    )
    ripening = ((h >= 5) & (h <= 25) & (s >= 50) & (v >= 40)).astype(np.uint8)
    return np.clip(red + green_fruit + ripening, 0, 1).astype(np.uint8)


def _banana_like_score(hsv: np.ndarray, gray: np.ndarray) -> float:
    """Elongated yellow object → banana-like. Yellow alone is not enough."""
    h, s, v = cv2.split(hsv)
    yellow = ((h >= 18) & (h <= 38) & (s >= 60) & (v >= 80)).astype(np.uint8) * 255
    if yellow.mean() < 8:
        return 0.0
    contours, _ = cv2.findContours(yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < 0.02 * gray.shape[0] * gray.shape[1]:
        return 0.0
    (_, _), (w, hh), _ = cv2.minAreaRect(c)
    if w < 1 or hh < 1:
        return 0.0
    elong = max(w, hh) / (min(w, hh) + 1e-6)
    yell_ratio = float(np.mean(yellow > 0))
    if elong < 2.0:
        return 0.0
    score = 0.35 * min(1.0, (elong - 2.0) / 2.0)
    score += 0.45 * min(1.0, yell_ratio / 0.2)
    if elong >= 3.0 and yell_ratio > 0.12:
        score += 0.25
    return float(np.clip(score, 0.0, 1.0))


def _citrus_orange_score(hsv: np.ndarray) -> float:
    """Strong saturated orange/yellow sphere-like citrus cue."""
    h, s, v = cv2.split(hsv)
    orange = ((h >= 8) & (h <= 25) & (s >= 100) & (v >= 90)).astype(np.uint8)
    return float(np.mean(orange))


def _apple_like_score(
    hsv: np.ndarray, fruit_shape: Dict[str, float], signals: Dict[str, float]
) -> float:
    """
    Apple / red-ball proxy using shape + surface + foliage context.
    Round red object with little green calyx/foliage and smooth body → high score.
    """
    circ = fruit_shape.get("circularity", 0.0)
    aspect = fruit_shape.get("aspect", 9.0)
    uniform = signals.get("fruit_uniformity", 0.0)
    veg = signals.get("vegetation_ratio", 0.0)
    red = signals.get("red_ratio", 0.0)
    tex = signals.get("texture", 0.0)

    if red < 0.10 or circ < 0.75 or aspect > 1.45:
        return 0.0

    score = 0.0
    score += 0.25  # base: round + red
    if veg < 0.025:
        score += 0.30  # missing calyx / foliage context
    elif veg < 0.04:
        score += 0.15
    if uniform >= 0.50:
        score += 0.22
    if uniform >= 0.70:
        score += 0.18
    if tex < 0.60:
        score += 0.10
    # Mottled tomato with any green calyx/foliage cue → less apple-like
    if veg >= 0.008 and tex >= 0.70:
        score *= 0.45
    return float(np.clip(score, 0.0, 1.0))


def _largest_blob_shape(mask: np.ndarray) -> Dict[str, float]:
    """Shape stats for largest foreground blob."""
    h, w = mask.shape
    area_img = float(h * w)
    if mask.dtype != np.uint8:
        mask_u8 = (mask > 0).astype(np.uint8) * 255
    else:
        mask_u8 = (mask > 0).astype(np.uint8) * 255

    # Clean small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {
            "coverage": 0.0,
            "circularity": 0.0,
            "aspect": 1.0,
            "extent": 0.0,
            "solidity": 0.0,
            "blob_count": 0.0,
        }

    areas = [cv2.contourArea(c) for c in contours]
    c = contours[int(np.argmax(areas))]
    area = float(cv2.contourArea(c))
    peri = float(cv2.arcLength(c, True)) + 1e-6
    circularity = float(np.clip(4.0 * np.pi * area / (peri * peri), 0.0, 1.0))
    x, y, bw, bh = cv2.boundingRect(c)
    aspect = float(max(bw, bh) / (min(bw, bh) + 1e-6))
    extent = float(area / (bw * bh + 1e-6))
    hull = cv2.convexHull(c)
    hull_area = float(cv2.contourArea(hull)) + 1e-6
    solidity = float(area / hull_area)
    # Significant blobs
    sig = sum(1 for a in areas if a > 0.01 * area_img)

    return {
        "coverage": float(np.clip(area / area_img, 0.0, 1.0)),
        "circularity": circularity,
        "aspect": aspect,
        "extent": extent,
        "solidity": solidity,
        "blob_count": float(sig),
    }


def _spatial_spread(mask: np.ndarray) -> float:
    """Prefer organic irregular spread over one solid rectangle (clothing)."""
    ys, xs = np.where(mask > 0)
    if len(xs) < 50:
        return 0.0
    # Coefficient of variation of coordinates → spread irregularity proxy
    cx = float(np.std(xs) / (np.mean(xs) + 1e-6))
    cy = float(np.std(ys) / (np.mean(ys) + 1e-6))
    return float(np.clip((cx + cy) / 2.0, 0.0, 1.0))


def _region_uniformity(gray: np.ndarray, mask: np.ndarray) -> float:
    """
    High when the masked region is nearly uniform (flat objects / drawings).
    Real tomato fruit/leaf tissue usually has more local variation.
    """
    m = mask > 0
    if int(np.count_nonzero(m)) < 80:
        return 0.0
    vals = gray[m].astype(np.float32)
    std = float(vals.std())
    # std ~0–8 → very flat; 15+ → more natural
    if std >= 22:
        return 0.0
    if std <= 6:
        return 1.0
    return float(np.clip((22.0 - std) / 16.0, 0.0, 1.0))


def _leaf_score(signals: Dict[str, float], shape: Dict[str, float]) -> float:
    veg = signals["vegetation_ratio"]
    tex = signals["texture"]
    circ = shape["circularity"]
    aspect = shape["aspect"]
    coverage = shape["coverage"]
    spread = signals["veg_spread"]
    banana = signals["banana"]
    citrus = signals["citrus"]
    doc = signals["document"]
    skin = signals["skin"]
    struct = signals["structure"]
    uniform = signals.get("veg_uniformity", 0.0)

    score = 0.0
    # Vegetation present but not entire flat field
    if 0.08 <= veg <= 0.95:
        score += 0.30 * min(1.0, veg / 0.22)
    # Natural / photographic texture (lenient for 224px crops)
    score += 0.18 * tex
    # Leaves are usually not near-perfect circles
    score += 0.10 * (1.0 - abs(circ - 0.45))
    # Mild elongation / irregular aspect OK
    if 1.02 <= aspect <= 3.8:
        score += 0.10
    # Decent subject coverage (close-up leaf)
    if 0.06 <= coverage <= 0.92:
        score += 0.14
    score += 0.10 * min(1.0, spread * 2.0)

    # Penalties
    score -= 0.55 * doc
    score -= 0.40 * max(0.0, skin - 0.18)
    score -= 0.25 * max(0.0, struct - 0.45)
    score -= 0.50 * banana
    score -= 0.15 * max(0.0, citrus - 0.18)
    # Too circular + red-heavy tends fruit, not leaf
    if circ > 0.78 and signals["fruit_color_ratio"] > 0.30 and signals.get("red_ratio", 0) > 0.15:
        score -= 0.25
    # Flat green clothing/wall: high veg + very uniform + ultra solid round/rect
    if veg > 0.50 and uniform > 0.65 and shape["solidity"] > 0.93 and tex < 0.35:
        score -= 0.40

    return float(np.clip(score, 0.0, 1.0))


def _leaf_like_penalty(
    signals: Dict[str, float], veg_shape: Dict[str, float], fruit_shape: Dict[str, float]
) -> float:
    """High when the subject looks like a leaf rather than a tomato fruit."""
    veg = signals["vegetation_ratio"]
    fruit_c = signals["fruit_color_ratio"]
    red = signals.get("red_ratio", 0.0)
    v_asp = veg_shape.get("aspect", 1.0)
    v_circ = veg_shape.get("circularity", 0.0)
    f_circ = fruit_shape.get("circularity", 0.0)
    f_asp = fruit_shape.get("aspect", 1.0)

    pen = 0.0
    if veg >= 0.28:
        pen += 0.25
    if veg >= 0.40:
        pen += 0.20
    if v_asp >= 1.35:
        pen += 0.20
    if v_circ > 0 and v_circ < 0.70 and veg >= 0.25:
        pen += 0.20
    if f_circ < 0.70 and veg >= 0.30:
        pen += 0.25
    if f_asp > 1.6 and red < 0.08:
        pen += 0.15
    if fruit_c >= 0.25 and red < 0.06 and veg >= 0.30:
        pen += 0.25

    # Round compact body → tomato fruit, not leaf canopy
    if f_circ >= 0.75 and f_asp <= 1.35:
        pen *= 0.30
    # Strong ripe-red subject with foliage in background is still fruit, not leaf
    if red >= 0.18:
        pen *= 0.35
    elif red >= 0.10:
        pen *= 0.55
    # Green tomato body (high fruit-color mass) is not a leaf canopy
    if fruit_c >= 0.30 and red < 0.10:
        pen *= 0.40
    elif fruit_c >= 0.22:
        pen *= 0.60
    return float(np.clip(pen, 0.0, 1.0))


def _fruit_score(signals: Dict[str, float], shape: Dict[str, float]) -> float:
    fruit_c = signals["fruit_color_ratio"]
    tex = signals["texture"]
    circ = shape["circularity"]
    aspect = shape["aspect"]
    coverage = shape["coverage"]
    banana = signals["banana"]
    citrus = signals["citrus"]
    doc = signals["document"]
    skin = signals["skin"]
    struct = signals["structure"]
    veg = signals["vegetation_ratio"]
    uniform = signals.get("fruit_uniformity", 0.0)
    red = signals.get("red_ratio", 0.0)
    leaf_like = signals.get("leaf_like_penalty", 0.0)
    apple_like = signals.get("apple_like", 0.0)

    score = 0.0
    if 0.06 <= fruit_c <= 0.95:
        score += 0.22 * min(1.0, fruit_c / 0.18)
    score += 0.12 * tex
    # Circularity helps but diseased / held tomatoes are often imperfect
    score += 0.22 * circ
    if aspect <= 1.70:
        score += 0.12
    else:
        score -= 0.25 * min(1.0, (aspect - 1.70) / 1.5)
    if 0.06 <= coverage <= 0.90:
        score += 0.10
    score += 0.08 * (1.0 - uniform)

    if red >= 0.18:
        score += 0.22
    elif red >= 0.08:
        score += 0.14
    elif circ >= 0.72 and aspect <= 1.45 and fruit_c >= 0.12:
        score += 0.08
    # Fragmented disease lesions can zero the fruit blob; still credit red mass
    if red >= 0.20 and circ < 0.45:
        score += 0.18
        score += 0.08 * min(1.0, red / 0.35)
    # Unripe / green tomato with substantial fruit-colored region
    if fruit_c >= 0.28 and red < 0.12 and circ >= 0.35:
        score += 0.16
    elif fruit_c >= 0.35 and coverage >= 0.12:
        score += 0.12

    # Document / UI bleed — lighter when a clear round fruit dominates
    doc_w = 0.25 if circ >= 0.75 and coverage >= 0.15 else 0.50
    score -= doc_w * doc
    score -= 0.45 * max(0.0, skin - 0.12)
    score -= 0.25 * max(0.0, struct - 0.45)
    score -= 0.65 * banana
    if citrus > 0.18 and red < 0.10:
        score -= 0.45
    score -= 0.45 * leaf_like
    score -= 0.55 * apple_like
    if veg > 0.40 and circ < 0.68:
        score -= 0.30
    if veg > 0.50 and red < 0.05 and circ < 0.72:
        score -= 0.25

    # Flat painted / apple / ball: near-uniform round red/orange body
    if circ >= 0.78 and uniform >= 0.85 and red >= 0.12:
        score -= 0.60
    elif circ >= 0.75 and uniform >= 0.70 and shape["solidity"] > 0.95 and red >= 0.10:
        score -= 0.40
    elif circ > 0.75 and uniform > 0.55 and shape["solidity"] > 0.93 and tex < 0.55:
        score -= 0.55

    return float(np.clip(score, 0.0, 1.0))


def _compute_signals(rgb: np.ndarray) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    veg = _vegetation_mask(hsv)
    fruit = _tomato_fruit_mask(hsv)
    h, s, v = cv2.split(hsv)
    red = (((h <= 12) | (h >= 165)) & (s >= 50) & (v >= 40)).astype(np.uint8)

    veg_shape = _largest_blob_shape(veg)
    fruit_shape = _largest_blob_shape(fruit)
    # Diseased tomatoes often fragment the fruit-color mask; fall back to red mass.
    if fruit_shape.get("coverage", 0.0) < 0.05 and float(np.mean(red > 0)) >= 0.12:
        red_shape = _largest_blob_shape(red)
        if red_shape.get("coverage", 0.0) > fruit_shape.get("coverage", 0.0):
            fruit_shape = red_shape

    signals = {
        "document": _document_screenshot_score(rgb, hsv, gray),
        "skin": _skin_score(hsv),
        "structure": _structure_score(gray),
        "texture": _texture_naturalness(gray),
        "vegetation_ratio": float(np.mean(veg > 0)),
        "fruit_color_ratio": float(np.mean(fruit > 0)),
        "red_ratio": float(np.mean(red > 0)),
        "banana": _banana_like_score(hsv, gray),
        "citrus": _citrus_orange_score(hsv),
        "veg_spread": _spatial_spread(veg),
        "veg_uniformity": _region_uniformity(gray, veg),
        "fruit_uniformity": _region_uniformity(gray, fruit),
        "sat_mean": _saturation_value_stats(hsv)[0],
        "val_mean": _saturation_value_stats(hsv)[1],
    }
    signals["leaf_like_penalty"] = _leaf_like_penalty(signals, veg_shape, fruit_shape)
    signals["apple_like"] = _apple_like_score(hsv, fruit_shape, signals)
    return signals, veg_shape, fruit_shape


def validate_crop_image(
    image_bytes: bytes,
    crop_part: str,
    *,
    leaf_threshold: float = 0.42,
    fruit_threshold: float = 0.48,
) -> PregateResult:
    """
    LEAF decision kept stable. FRUIT is stricter and modality-exclusive.
    """
    crop = (crop_part or "").strip().upper()
    reject_msg = (
        REJECT_MESSAGE_FRUIT
        if crop == "FRUIT"
        else (REJECT_MESSAGE_LEAF if crop == "LEAF" else REJECT_MESSAGE)
    )
    rgb = _decode(image_bytes)
    if rgb is None:
        return PregateResult(False, 0.0, reject_msg, {"decode": 0.0})

    signals, veg_shape, fruit_shape = _compute_signals(rgb)

    if signals["document"] >= 0.55:
        return PregateResult(
            False,
            round(1.0 - signals["document"], 4),
            reject_msg,
            {**signals, "leaf_score": 0.0, "fruit_score": 0.0, "hard": 1.0},
        )
    # Skin / face: LEAF keeps hard reject. FRUIT allows a hand holding a tomato.
    if signals["skin"] >= 0.42:
        if crop == "FRUIT":
            sat = signals.get("sat_mean", 0.0)
            tex = signals.get("texture", 0.0)
            red = signals.get("red_ratio", 0.0)
            fruit_c0 = signals.get("fruit_color_ratio", 0.0)
            held_tomato = (red >= 0.15 or fruit_c0 >= 0.22) and sat >= 0.22 and tex >= 0.40
            if not held_tomato:
                return PregateResult(
                    False,
                    round(1.0 - signals["skin"], 4),
                    reject_msg,
                    {**signals, "leaf_score": 0.0, "fruit_score": 0.0, "hard": 1.0},
                )
        else:
            return PregateResult(
                False,
                round(1.0 - signals["skin"], 4),
                reject_msg,
                {**signals, "leaf_score": 0.0, "fruit_score": 0.0, "hard": 1.0},
            )
    # FRUIT: reject faces / skin-dominant frames. Allow a hand holding a ripe tomato
    # (skin on the edge + high-sat red fruit + natural texture).
    if crop == "FRUIT" and signals["skin"] >= 0.28:
        sat = signals.get("sat_mean", 0.0)
        tex = signals.get("texture", 0.0)
        red = signals.get("red_ratio", 0.0)
        fruit_c0 = signals.get("fruit_color_ratio", 0.0)
        held_tomato = (
            (red >= 0.18 or fruit_c0 >= 0.22) and sat >= 0.24 and tex >= 0.45
        )
        if not held_tomato:
            return PregateResult(
                False,
                round(1.0 - signals["skin"], 4),
                reject_msg,
                {**signals, "leaf_score": 0.0, "fruit_score": 0.0, "hard": 1.0},
            )
    if signals["banana"] >= 0.55:
        return PregateResult(
            False,
            round(1.0 - signals["banana"], 4),
            reject_msg,
            {**signals, "leaf_score": 0.0, "fruit_score": 0.0, "hard": 1.0},
        )
    if (
        signals["structure"] >= 0.75
        and signals["vegetation_ratio"] < 0.12
        and signals["fruit_color_ratio"] < 0.12
    ):
        return PregateResult(
            False,
            round(1.0 - signals["structure"], 4),
            reject_msg,
            {**signals, "leaf_score": 0.0, "fruit_score": 0.0, "hard": 1.0},
        )

    leaf_s = _leaf_score(signals, veg_shape)
    fruit_s = _fruit_score(signals, fruit_shape)
    details = {
        **signals,
        **{f"veg_{k}": v for k, v in veg_shape.items()},
        **{f"fruit_{k}": v for k, v in fruit_shape.items()},
        "leaf_score": leaf_s,
        "fruit_score": fruit_s,
    }

    if crop == "LEAF":
        citrus = signals.get("citrus", 0.0)
        apple_like = signals.get("apple_like", 0.0)
        veg_circ = veg_shape.get("circularity", 0.0)
        fruit_circ = fruit_shape.get("circularity", 0.0)
        veg_uni = signals.get("veg_uniformity", 0.0)
        red = signals.get("red_ratio", 0.0)
        blob_circ = max(veg_circ, fruit_circ)
        blob_aspect = min(veg_shape.get("aspect", 9.0), fruit_shape.get("aspect", 9.0))

        # Citrus/orange sphere — not a tomato leaf
        hard_citrus = citrus >= 0.28 and blob_circ >= 0.72
        # Smooth round non-leaf object (apple, orange, ball) with little red tomato hue
        hard_sphere = (
            blob_circ >= 0.78
            and blob_aspect <= 1.35
            and veg_uni >= 0.55
            and leaf_s < 0.62
            and red < 0.12
        )
        hard_apple = apple_like >= 0.45
        # Strong round-fruit cues beating leaf score (wrong modality)
        hard_fruit_modality = (
            fruit_s >= 0.34
            and leaf_s <= fruit_s + 0.12
            and blob_circ >= 0.72
            and citrus >= 0.22
        )

        if hard_citrus or hard_sphere or hard_apple or hard_fruit_modality:
            return PregateResult(
                False,
                round(max(0.0, 1.0 - leaf_s), 4),
                reject_msg,
                details,
            )

        ok = leaf_s >= leaf_threshold and leaf_s >= fruit_s - 0.08
        conf = leaf_s if ok else max(0.0, 1.0 - leaf_s)
        return PregateResult(
            ok,
            round(float(conf), 4),
            None if ok else reject_msg,
            details,
        )

    if crop == "FRUIT":
        leaf_like = signals.get("leaf_like_penalty", 0.0)
        circ = fruit_shape.get("circularity", 0.0)
        aspect = fruit_shape.get("aspect", 9.0)
        coverage = fruit_shape.get("coverage", 0.0)
        red = signals.get("red_ratio", 0.0)
        veg = signals["vegetation_ratio"]
        fruit_c = signals["fruit_color_ratio"]
        tex = signals.get("texture", 0.0)

        # Leaf photo: green canopy with little fruit-colored mass.
        # Green tomatoes have high fruit_c — do not treat them as leaves.
        hard_leaf = (
            leaf_like >= 0.55 and red < 0.10 and veg >= 0.32 and fruit_c < 0.22
        ) or (veg >= 0.55 and red < 0.06 and fruit_c < 0.14 and circ < 0.42)

        # Roma / plum tomatoes are elongated — allow higher aspect than apples.
        hard_shape = aspect > 3.05 or (
            circ < 0.32 and red < 0.10 and fruit_c < 0.16 and coverage < 0.08
        )
        hard_apple = signals.get("apple_like", 0.0) >= 0.52 or (
            signals.get("apple_like", 0.0) >= 0.48
            and signals.get("fruit_uniformity", 0.0) >= 0.52
            and veg < 0.02
            and circ >= 0.84
            and red >= 0.25
        )
        citrus = signals.get("citrus", 0.0)
        # Orange / citrus sphere: strong orange hue, little ripe-tomato red
        hard_citrus = citrus >= 0.32 and red < 0.10

        # Ripe or green fruit mass can beat foliage leaf_score
        if red >= 0.14 or fruit_c >= 0.28:
            beats_leaf = fruit_s + 0.28 >= leaf_s
        else:
            beats_leaf = fruit_s >= leaf_s + 0.06

        score_ok = fruit_s >= fruit_threshold or (
            red >= 0.14 and fruit_s >= max(0.26, fruit_threshold - 0.20)
        ) or (
            fruit_c >= 0.28
            and tex >= 0.30
            and fruit_s >= max(0.24, fruit_threshold - 0.22)
            and citrus < 0.28
        )
        color_ok = (
            red >= 0.05
            or (
                fruit_c >= 0.16
                and circ >= 0.40
                and aspect <= 2.90
                and leaf_like < 0.55
                and citrus < 0.30
            )
            or (
                fruit_c >= 0.28
                and coverage >= 0.10
                and aspect <= 3.05
                and citrus < 0.28
            )
        )
        # Compact tomato / Roma body OR clear fruit-color mass
        body_ok = (circ >= 0.38 and aspect <= 3.05) or (
            (red >= 0.12 or fruit_c >= 0.22)
            and (coverage >= 0.05 or fruit_c >= 0.18)
        )

        ok = bool(
            score_ok
            and beats_leaf
            and color_ok
            and body_ok
            and not hard_leaf
            and not hard_shape
            and not hard_apple
            and not hard_citrus
        )
        conf = fruit_s if ok else max(0.0, 1.0 - fruit_s)
        return PregateResult(
            ok,
            round(float(conf), 4),
            None if ok else reject_msg,
            details,
        )

    return PregateResult(False, 0.0, REJECT_MESSAGE, details)


def is_valid_tomato_image(
    image_bytes: bytes, crop_part: str
) -> Tuple[bool, float, Optional[str]]:
    """Public tuple API matching gate_predictor style."""
    result = validate_crop_image(image_bytes, crop_part)
    return result.accepted, result.confidence, result.reason
