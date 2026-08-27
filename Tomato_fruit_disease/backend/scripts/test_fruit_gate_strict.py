"""
Strict FRUIT gate regression tests (no retrain).

Usage (from backend/):
  python scripts/test_fruit_gate_strict.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from ml.predict.cv_pregate import (  # noqa: E402
    REJECT_MESSAGE_FRUIT,
    validate_crop_image,
)
from ml.predict.gate_predictor import is_valid_fruit, is_valid_leaf  # noqa: E402


def _jpeg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _apple_regression() -> bytes:
    """Canonical apple false-positive regression sample."""
    img = Image.new("RGB", (320, 320), (245, 245, 245))
    d = ImageDraw.Draw(img)
    d.ellipse([50, 50, 270, 270], fill=(200, 40, 30))
    d.rectangle([155, 30, 170, 55], fill=(40, 120, 40))
    d.ellipse([90, 90, 120, 120], fill=(220, 70, 55))
    return _jpeg(img)


def _textured_apple() -> bytes:
    arr = np.zeros((320, 320, 3), dtype=np.uint8)
    arr[:, :] = (240, 240, 240)
    yy, xx = np.ogrid[:320, :320]
    mask = (xx - 160) ** 2 + (yy - 165) ** 2 <= 110**2
    rng = np.random.RandomState(3)
    base = np.zeros_like(arr)
    base[mask] = (210, 45, 40)
    noise = rng.normal(0, 12, base.shape).astype(np.int16)
    tint = np.zeros_like(base)
    tint[mask] = (30, 20, 0)
    out = np.clip(base.astype(np.int16) + noise + tint, 0, 255)
    h = (xx - 120) ** 2 + (yy - 120) ** 2 <= 25**2
    out[h & mask] = np.clip(out[h & mask] + 40, 0, 255)
    arr[mask] = out[mask].astype(np.uint8)
    arr[145:160, 155:165] = (50, 100, 40)
    return _jpeg(Image.fromarray(arr))


def _banana() -> bytes:
    img = Image.new("RGB", (400, 220), (245, 245, 245))
    d = ImageDraw.Draw(img)
    d.ellipse([20, 60, 380, 160], fill=(240, 210, 40))
    return _jpeg(img)


def _orange() -> bytes:
    img = Image.new("RGB", (320, 320), (245, 245, 245))
    d = ImageDraw.Draw(img)
    d.ellipse([40, 40, 280, 280], fill=(245, 140, 30))
    return _jpeg(img)


def _face() -> bytes:
    img = Image.new("RGB", (320, 320), (240, 240, 240))
    d = ImageDraw.Draw(img)
    d.ellipse([60, 40, 260, 280], fill=(210, 160, 130))
    d.ellipse([110, 120, 140, 150], fill=(40, 30, 30))
    d.ellipse([180, 120, 210, 150], fill=(40, 30, 30))
    return _jpeg(img)


def _document() -> bytes:
    img = Image.new("RGB", (400, 520), (250, 250, 252))
    d = ImageDraw.Draw(img)
    for y in range(40, 500, 22):
        d.rectangle([30, y, 370, y + 10], fill=(20, 20, 20))
    return _jpeg(img)


def _building() -> bytes:
    img = Image.new("RGB", (360, 360), (170, 180, 190))
    d = ImageDraw.Draw(img)
    for x in range(20, 340, 36):
        d.rectangle([x, 30, x + 24, 330], outline=(30, 30, 30), width=2)
        for y in range(50, 310, 28):
            d.rectangle([x + 4, y, x + 20, y + 14], fill=(220, 230, 240))
    return _jpeg(img)


def _red_ball() -> bytes:
    img = Image.new("RGB", (300, 300), (230, 230, 230))
    d = ImageDraw.Draw(img)
    d.ellipse([40, 40, 260, 260], fill=(220, 30, 30))
    return _jpeg(img)


def _green_tomato() -> bytes:
    arr = np.zeros((320, 320, 3), dtype=np.uint8)
    arr[:, :] = (245, 245, 245)
    yy, xx = np.ogrid[:320, :320]
    mask = (xx - 160) ** 2 + (yy - 160) ** 2 <= 115**2
    base = np.zeros_like(arr)
    base[mask] = (45, 150, 55)
    rng = np.random.RandomState(7)
    mottling = rng.normal(0, 16, base.shape).astype(np.int16)
    dist = np.sqrt((xx - 130) ** 2 + (yy - 130) ** 2)
    shade = ((130 - dist) * 0.22).clip(-28, 32).astype(np.int16)
    shade3 = np.stack([shade, shade, shade], axis=-1)
    out = base.astype(np.int16)
    out[mask] = np.clip(out[mask] + mottling[mask] + shade3[mask], 0, 255)
    arr[mask] = out[mask].astype(np.uint8)
    return _jpeg(Image.fromarray(arr))


def _red_tomato() -> bytes:
    arr = np.zeros((320, 320, 3), dtype=np.uint8)
    arr[:, :] = (245, 245, 245)
    yy, xx = np.ogrid[:320, :320]
    mask = (xx - 160) ** 2 + (yy - 160) ** 2 <= 115**2
    base = np.zeros_like(arr)
    base[mask] = (190, 35, 35)
    rng = np.random.RandomState(11)
    mottling = rng.normal(0, 14, base.shape).astype(np.int16)
    dist = np.sqrt((xx - 125) ** 2 + (yy - 125) ** 2)
    shade = ((120 - dist) * 0.2).clip(-25, 35).astype(np.int16)
    shade3 = np.stack([shade, shade, shade], axis=-1)
    out = base.astype(np.int16)
    out[mask] = np.clip(out[mask] + mottling[mask] + shade3[mask], 0, 255)
    # Visible green calyx / sepal cluster (tomato cue)
    for cx, cy, r in ((160, 72, 16), (148, 78, 10), (172, 78, 10)):
        calyx = (xx - cx) ** 2 + (yy - cy) ** 2 <= r**2
        out[calyx] = (40, 120, 45)
    arr[...] = np.clip(out, 0, 255).astype(np.uint8)
    return _jpeg(Image.fromarray(arr))


def _tomato_leaf_bytes():
    p = BACKEND / "data" / "observations" / "CASE-2783DA2A" / "OBS-AB097DEF.jpg"
    return p.read_bytes() if p.exists() else None


def _check(name: str, data: bytes, crop: str, expect_accept: bool) -> bool:
    r = validate_crop_image(data, crop)
    if crop == "FRUIT":
        ok, _, reason = is_valid_fruit(data)
    else:
        ok, _, reason = is_valid_leaf(data)
    passed = (ok == expect_accept) and (r.accepted == expect_accept)
    if expect_accept is False and crop == "FRUIT" and reason:
        passed = passed and ("fruit" in reason.lower())
    tag = "PASS" if passed else "FAIL"
    print(
        f"[{tag}] {name:22s} crop={crop:5s} expect={'ACCEPT' if expect_accept else 'REJECT'} "
        f"got={'ACCEPT' if ok else 'REJECT'} "
        f"leaf={r.details.get('leaf_score', 0):.2f} fruit={r.details.get('fruit_score', 0):.2f} "
        f"leaf_like={r.details.get('leaf_like_penalty', 0):.2f}"
    )
    if not expect_accept and crop == "FRUIT" and ok is False:
        assert reason == REJECT_MESSAGE_FRUIT or (reason and "fruit" in reason.lower())
    return passed


def main():
    results = []
    leaf = _tomato_leaf_bytes()

    # FRUIT accepts
    results.append(_check("green_tomato", _green_tomato(), "FRUIT", True))
    results.append(_check("red_tomato", _red_tomato(), "FRUIT", True))

    # FRUIT rejects
    results.append(_check("apple_regression", _apple_regression(), "FRUIT", False))
    results.append(_check("textured_apple", _textured_apple(), "FRUIT", False))
    results.append(_check("banana", _banana(), "FRUIT", False))
    results.append(_check("orange", _orange(), "FRUIT", False))
    results.append(_check("face", _face(), "FRUIT", False))
    results.append(_check("document", _document(), "FRUIT", False))
    results.append(_check("building", _building(), "FRUIT", False))
    results.append(_check("red_ball", _red_ball(), "FRUIT", False))

    if leaf is not None:
        # Critical: leaf must reject in FRUIT, accept in LEAF
        results.append(_check("tomato_leaf_in_FRUIT", leaf, "FRUIT", False))
        results.append(_check("tomato_leaf_in_LEAF", leaf, "LEAF", True))
        # Fruit image should not pass as LEAF (green tomato may still look leafy — soft check)
        r = validate_crop_image(_green_tomato(), "LEAF")
        print(
            f"[INFO] green_tomato as LEAF accepted={r.accepted} "
            f"leaf={r.details.get('leaf_score', 0):.2f} fruit={r.details.get('fruit_score', 0):.2f}"
        )
    else:
        print("[SKIP] tomato leaf observation image missing")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks matched expectation")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
