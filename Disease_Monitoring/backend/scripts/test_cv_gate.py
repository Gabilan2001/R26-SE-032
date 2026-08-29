"""
Manual / CI helper: test CV+gate accept/reject without retraining.

Usage (from backend/):
  python scripts/test_cv_gate.py
  python scripts/test_cv_gate.py --leaf path/to/leaf.jpg --fruit path/to/fruit.jpg

Synthetic negatives are generated in-memory (no dataset download).
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from ml.predict.cv_pregate import validate_crop_image  # noqa: E402
from ml.predict.gate_predictor import is_valid_fruit, is_valid_leaf  # noqa: E402


def _jpeg_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _solid(color, size=(320, 320)) -> bytes:
    return _jpeg_bytes(Image.new("RGB", size, color))


def _document_image() -> bytes:
    img = Image.new("RGB", (480, 640), (250, 250, 252))
    draw = ImageDraw.Draw(img)
    for i, y in enumerate(range(40, 600, 28)):
        draw.rectangle([40, y, 440, y + 14], fill=(30, 30, 30))
        if i % 3 == 0:
            draw.line([40, y + 20, 440, y + 20], fill=(180, 180, 180), width=1)
    draw.rectangle([40, 40, 440, 100], outline=(0, 0, 0), width=2)
    draw.text((50, 55), "Test Schedule / Receipt", fill=(0, 0, 0))
    return _jpeg_bytes(img)


def _face_like() -> bytes:
    """Skin-tone oval approximating a face crop (no real photo)."""
    img = Image.new("RGB", (320, 320), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.ellipse([60, 40, 260, 280], fill=(210, 160, 130))
    draw.ellipse([110, 120, 140, 150], fill=(40, 30, 30))
    draw.ellipse([180, 120, 210, 150], fill=(40, 30, 30))
    draw.arc([120, 170, 200, 230], 20, 160, fill=(120, 60, 60), width=4)
    return _jpeg_bytes(img)


def _banana_like() -> bytes:
    img = Image.new("RGB", (400, 220), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.ellipse([20, 60, 380, 160], fill=(240, 210, 40))
    return _jpeg_bytes(img)


def _building_like() -> bytes:
    img = Image.new("RGB", (400, 400), (180, 190, 200))
    draw = ImageDraw.Draw(img)
    for x in range(20, 380, 40):
        draw.rectangle([x, 40, x + 28, 360], outline=(40, 40, 40), width=2)
        for y in range(60, 340, 30):
            draw.rectangle([x + 4, y, x + 24, y + 16], fill=(220, 230, 240))
    return _jpeg_bytes(img)


def _apple_like() -> bytes:
    """Round saturated red object with near-uniform fill (apple/object proxy)."""
    img = Image.new("RGB", (320, 320), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 270, 270], fill=(200, 40, 30))
    draw.rectangle([155, 30, 170, 55], fill=(40, 120, 40))
    # Tiny highlight only — still nearly uniform body
    draw.ellipse([90, 90, 120, 120], fill=(220, 70, 55))
    return _jpeg_bytes(img)


def _orange_like() -> bytes:
    """Saturated orange sphere (citrus proxy)."""
    img = Image.new("RGB", (320, 320), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.ellipse([40, 40, 280, 280], fill=(245, 140, 30))
    return _jpeg_bytes(img)


def _other_leaf_like() -> bytes:
    """Flat green rectangle with low organic texture (clothing/other plant proxy)."""
    arr = np.zeros((320, 320, 3), dtype=np.uint8)
    arr[:, :] = (30, 140, 50)
    # Almost flat — little vein texture
    noise = np.random.RandomState(0).randint(-3, 4, arr.shape, dtype=np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return _jpeg_bytes(Image.fromarray(arr))


def _find_default_leaf():
    # Prefer real saved observations over synthetic PlantVillage stubs
    obs = BACKEND / "data" / "observations"
    preferred = [
        obs / "CASE-2783DA2A" / "OBS-AB097DEF.jpg",
        obs / "CASE-3AC26ECA" / "OBS-4C750FBE.jpg",
    ]
    for p in preferred:
        if p.exists():
            return p
    if obs.exists():
        for p in obs.rglob("*.jpg"):
            return p
    candidates = [
        BACKEND / "datasets" / "PlantVillage" / "Tomato_Early_blight",
        BACKEND / "datasets" / "PlantVillage" / "Tomato_healthy",
    ]
    for folder in candidates:
        if not folder.exists():
            continue
        for p in sorted(folder.glob("*")):
            if p.suffix.lower() in {".png", ".jpg", ".jpeg"} and "synthetic" not in p.name.lower():
                return p
        # fallback to synthetic if that is all we have
        for p in sorted(folder.glob("*")):
            if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                return p
    return None


def _find_default_fruit():
    # Prefer dedicated fruit folders only — do NOT reuse leaf observation images
    for folder_name in ("Tomato_fruit", "fruit", "tomatoes"):
        folder = BACKEND / "datasets" / folder_name
        if folder.exists():
            for p in folder.rglob("*"):
                if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                    return p
    return None


def _run_case(name: str, crop: str, data: bytes, expect_accept: bool) -> bool:
    cv = validate_crop_image(data, crop)
    if crop == "LEAF":
        ok, conf, reason = is_valid_leaf(data)
    else:
        ok, conf, reason = is_valid_fruit(data)
    status = "PASS" if ok == expect_accept else "FAIL"
    print(
        f"[{status}] {name:18s} crop={crop:5s} expect={'ACCEPT' if expect_accept else 'REJECT'} "
        f"got={'ACCEPT' if ok else 'REJECT'} cv={cv.details.get('leaf_score' if crop=='LEAF' else 'fruit_score', 0):.2f} "
        f"conf={conf} reason={reason!r}"
    )
    return ok == expect_accept


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--leaf", type=Path, default=None)
    parser.add_argument("--fruit", type=Path, default=None)
    args = parser.parse_args()

    leaf_path = args.leaf or _find_default_leaf()
    fruit_path = args.fruit or _find_default_fruit()

    results = []

    if leaf_path and leaf_path.exists():
        results.append(
            _run_case("tomato_leaf", "LEAF", leaf_path.read_bytes(), True)
        )
    else:
        print("[SKIP] tomato_leaf — no sample path found (pass --leaf)")

    if fruit_path and fruit_path.exists():
        results.append(
            _run_case("tomato_fruit", "FRUIT", fruit_path.read_bytes(), True)
        )
    else:
        print("[SKIP] tomato_fruit — no sample path found (pass --fruit)")
        # Synthetic mottled green tomato (surface variation, not flat paint)
        arr = np.zeros((320, 320, 3), dtype=np.uint8)
        arr[:, :] = (245, 245, 245)
        yy, xx = np.ogrid[:320, :320]
        mask = (xx - 160) ** 2 + (yy - 160) ** 2 <= 120**2
        base = np.zeros_like(arr)
        base[mask] = (45, 150, 55)
        rng = np.random.RandomState(7)
        mottling = rng.normal(0, 18, base.shape).astype(np.int16)
        # radial highlight / shadow for 3D cue
        dist = np.sqrt((xx - 130) ** 2 + (yy - 130) ** 2)
        shade = ((140 - dist) * 0.25).clip(-30, 35).astype(np.int16)
        shade3 = np.stack([shade, shade, shade], axis=-1)
        out = base.astype(np.int16)
        out[mask] = np.clip(out[mask] + mottling[mask] + shade3[mask], 0, 255)
        arr[mask] = out[mask].astype(np.uint8)
        results.append(
            _run_case("synth_green_tomato", "FRUIT", _jpeg_bytes(Image.fromarray(arr)), True)
        )

    results.append(_run_case("apple_like", "FRUIT", _apple_like(), False))
    results.append(_run_case("apple_like_LEAF", "LEAF", _apple_like(), False))
    results.append(_run_case("orange_like_LEAF", "LEAF", _orange_like(), False))
    results.append(_run_case("banana_like", "FRUIT", _banana_like(), False))
    results.append(_run_case("other_leaf_flat", "LEAF", _other_leaf_like(), False))
    results.append(_run_case("face_like", "LEAF", _face_like(), False))
    results.append(_run_case("document", "LEAF", _document_image(), False))
    results.append(_run_case("building", "LEAF", _building_like(), False))
    results.append(_run_case("document_fruit", "FRUIT", _document_image(), False))

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks matched expectation")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
