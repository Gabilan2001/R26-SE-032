"""
Quick U-Net leaf severity test.

Usage:
  python tests/test_unet_leaf.py path/to/leaf.jpg

If no image path is provided, it runs a synthetic in-memory smoke test.
"""

import io
import os
import sys

from PIL import Image, ImageDraw

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from ml.predict.unet_predictor import get_leaf_severity


def _load_image_bytes():
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        with open(image_path, "rb") as image_file:
            return image_file.read(), image_path

    image = Image.new("RGB", (256, 256), (40, 120, 40))
    draw = ImageDraw.Draw(image)
    draw.ellipse((50, 30, 205, 230), fill=(30, 150, 35))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue(), "synthetic-smoke-test"


def main():
    image_bytes, label = _load_image_bytes()
    print(f"Testing U-Net leaf severity on: {label}")

    severity_a, confidence_a = get_leaf_severity(image_bytes, "A")
    severity_b, confidence_b = get_leaf_severity(image_bytes, "B")

    print(f"Disease A severity: {severity_a}%")
    print(f"Disease A confidence: {confidence_a}")
    print(f"Disease B severity: {severity_b}%")
    print(f"Disease B confidence: {confidence_b}")


if __name__ == "__main__":
    main()
