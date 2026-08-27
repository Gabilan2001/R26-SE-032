"""
Test OpenCV affected-area severity (no retrain).

Usage (from backend/):
  python scripts/test_cv_area_severity.py
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

from ml.predict.cv_pregate import is_valid_tomato_image  # noqa: E402
from severity.cv_area_severity import estimate_affected_area  # noqa: E402
from severity.leaf.efficientnet_severity import predict_leaf_severity  # noqa: E402


def _jpeg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _healthy_leaf() -> bytes:
    """Mostly uniform green leaf-like region."""
    arr = np.zeros((320, 320, 3), dtype=np.uint8)
    arr[:, :] = (240, 240, 240)
    yy, xx = np.ogrid[:320, :320]
    mask = ((xx - 160) / 110) ** 2 + ((yy - 160) / 130) ** 2 <= 1.0
    base = np.zeros_like(arr)
    base[mask] = (40, 140, 55)
    rng = np.random.RandomState(1)
    noise = rng.randint(-8, 9, base.shape)
    out = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    arr[mask] = out[mask]
    return _jpeg(Image.fromarray(arr))


def _mild_leaf() -> bytes:
    """Healthy green with small brown spots (~low %)."""
    arr = np.array(Image.open(io.BytesIO(_healthy_leaf())).convert("RGB"))
    # sprinkle small lesions
    for cx, cy, r in [(120, 140, 8), (180, 200, 7), (150, 110, 6)]:
        yy, xx = np.ogrid[:320, :320]
        m = (xx - cx) ** 2 + (yy - cy) ** 2 <= r**2
        arr[m] = (90, 55, 25)
    return _jpeg(Image.fromarray(arr))


def _severe_leaf() -> bytes:
    """Large necrotic / chlorotic patches."""
    arr = np.array(Image.open(io.BytesIO(_healthy_leaf())).convert("RGB"))
    yy, xx = np.ogrid[:320, :320]
    m1 = (xx - 140) ** 2 + (yy - 150) ** 2 <= 55**2
    m2 = (xx - 190) ** 2 + (yy - 200) ** 2 <= 45**2
    arr[m1] = (70, 45, 20)
    arr[m2] = (180, 160, 40)
    return _jpeg(Image.fromarray(arr))


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


def _green_tomato() -> bytes:
    """Round mottled green tomato for fruit severity smoke."""
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
    # dark lesion blotch
    lesion = (xx - 190) ** 2 + (yy - 200) ** 2 <= 28**2
    out[lesion & mask] = (40, 35, 20)
    arr[mask] = out[mask].astype(np.uint8)
    return _jpeg(Image.fromarray(arr))


def _print_case(name: str, crop: str, data: bytes, expect_low=None):
    gate_ok, _, gate_reason = is_valid_tomato_image(data, crop)
    if not gate_ok:
        print(f"[GATE-REJECT] {name:16s} {gate_reason}")
        return True  # expected for junk
    area = estimate_affected_area(data, crop)
    pct = area["estimated_affected_area_percentage"]
    cls = area["severity_class"]
    ok = True
    if expect_low is True and cls != "LOW":
        ok = False
    if expect_low is False and cls != "HIGH":
        ok = False
    tag = "PASS" if ok else "FAIL"
    print(
        f"[{tag}] {name:16s} crop={crop} pct={pct:5.1f}% class={cls} "
        f"subj={area['subject_pixels']} aff={area['affected_pixels']}"
    )
    return ok


def main():
    results = []
    # Prefer real observation if available
    leaf_path = BACKEND / "data" / "observations" / "CASE-2783DA2A" / "OBS-AB097DEF.jpg"
    if leaf_path.exists():
        data = leaf_path.read_bytes()
        area = estimate_affected_area(data, "LEAF")
        full = predict_leaf_severity(data)
        print(
            f"[INFO] real_leaf_obs pct={area['estimated_affected_area_percentage']}% "
            f"class={area['severity_class']} cnn_p={full.get('cnn_high_prob')} "
            f"score={full['severity_score']} emb_dim={len(full['embedding'])}"
        )

    results.append(_print_case("healthy_leaf", "LEAF", _healthy_leaf(), expect_low=True))
    results.append(_print_case("mild_leaf", "LEAF", _mild_leaf(), expect_low=True))
    results.append(_print_case("severe_leaf", "LEAF", _severe_leaf(), expect_low=False))
    results.append(_print_case("fruit_tomato", "FRUIT", _green_tomato(), expect_low=None))

    # Gate rejects before severity in real pipeline
    for name, data in (("document", _document()), ("building", _building())):
        ok, _, reason = is_valid_tomato_image(data, "LEAF")
        passed = (ok is False)
        print(f"[{'PASS' if passed else 'FAIL'}] {name:16s} gate_reject={not ok} {reason}")
        results.append(passed)

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks matched expectation")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
