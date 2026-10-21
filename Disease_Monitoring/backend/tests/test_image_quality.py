"""Image quality pre-check tests."""

import io

import cv2
import numpy as np
from PIL import Image

from utils.image_quality import analyze_image_quality


def _jpeg_bytes(arr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", arr)
    assert ok
    return buf.tobytes()


def _solid(w: int, h: int, color=(120, 140, 80)) -> bytes:
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = color
    return _jpeg_bytes(img)


def test_sharp_leaf_like_passes_blur():
    rng = np.random.default_rng(0)
    img = rng.integers(40, 200, (640, 640, 3), dtype=np.uint8)
    result = analyze_image_quality(_jpeg_bytes(img), "LEAF")
    assert result["checks"]["blur"]["status"] in ("pass", "warn")


def test_blurred_image_warns_or_fails():
    rng = np.random.default_rng(1)
    img = rng.integers(40, 200, (640, 640, 3), dtype=np.uint8)
    blurred = cv2.GaussianBlur(img, (31, 31), 0)
    result = analyze_image_quality(_jpeg_bytes(blurred), "LEAF")
    assert result["checks"]["blur"]["status"] in ("warn", "fail")


def test_dark_image_warns_brightness():
    dark = np.full((640, 640, 3), 15, dtype=np.uint8)
    result = analyze_image_quality(_jpeg_bytes(dark), "LEAF")
    assert result["checks"]["brightness"]["status"] == "warn"


def test_low_resolution_warns_distance():
    result = analyze_image_quality(_solid(300, 400), "LEAF")
    assert result["checks"]["distance"]["status"] == "warn"
    assert result["can_upload"] is True


def test_overall_summary_present():
    result = analyze_image_quality(_solid(800, 800), "FRUIT")
    assert result["ok"] is True
    assert result["farmer_summary"]
    assert result["overall"] in ("good", "fair", "poor")
