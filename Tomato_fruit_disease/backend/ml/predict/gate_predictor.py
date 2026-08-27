"""
Gate Predictor — tomato leaf / fruit validation.

Pipeline (no retraining):
  1) Deterministic OpenCV pre-gate (cv_pregate) — hard reject unrelated images
  2) Optional MobileNet gate as secondary check (existing weights, not retrained)

IMAGE_GATE_MODE:
  hybrid (default) — CV must pass; MobileNet confidence is advisory only
  strict           — CV must pass AND MobileNet must pass
  soft             — CV must still pass; MobileNet soft-accept disabled for CV
  off              — skip validation (decode-only); debug only

Rejected images never reach severity inference (enforced by observation_service).
"""

import os
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import io
from typing import Optional

from ml.predict.cv_pregate import (
    REJECT_MESSAGE,
    REJECT_MESSAGE_FRUIT,
    is_valid_tomato_image,
)

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
LEAF_MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "gate_leaf.pth")
FRUIT_MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "gate_fruit.pth")

LEAF_GATE_THRESHOLD = float(os.getenv("LEAF_GATE_THRESHOLD", "0.5"))
FRUIT_GATE_THRESHOLD = float(os.getenv("FRUIT_GATE_THRESHOLD", "0.5"))
# hybrid: CV hard-gate (fixes soft-accept of junk images)
IMAGE_GATE_MODE = os.getenv("IMAGE_GATE_MODE", "hybrid").strip().lower()

_leaf_model = None
_fruit_model = None


def _gate_mode() -> str:
    mode = os.getenv("IMAGE_GATE_MODE", IMAGE_GATE_MODE).strip().lower()
    if mode not in {"hybrid", "strict", "soft", "off"}:
        return "hybrid"
    return mode


def _load_leaf_model():
    global _leaf_model
    if _leaf_model is not None:
        return _leaf_model

    if not os.path.exists(LEAF_MODEL_PATH):
        print(f"WARNING: gate_leaf.pth not found at {LEAF_MODEL_PATH}")
        return None

    model = models.mobilenet_v2(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.last_channel, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, 1),
    )
    model.load_state_dict(torch.load(LEAF_MODEL_PATH, map_location="cpu"))
    model.eval()
    _leaf_model = model
    print("Gate leaf model loaded successfully")
    return model


_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225],
    ),
])


def _load_fruit_model():
    global _fruit_model
    if _fruit_model is not None:
        return _fruit_model

    if not os.path.exists(FRUIT_MODEL_PATH):
        print(f"WARNING: gate_fruit.pth not found at {FRUIT_MODEL_PATH}")
        return None

    model = models.mobilenet_v2(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.last_channel, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, 1),
    )
    model.load_state_dict(torch.load(FRUIT_MODEL_PATH, map_location="cpu"))
    model.eval()
    _fruit_model = model
    print("Gate fruit model loaded successfully")
    return model


def reload_leaf_gate():
    """Force reload after retraining."""
    global _leaf_model
    _leaf_model = None
    return _load_leaf_model()


def _ml_prob_leaf(image_bytes: bytes):
    model = _load_leaf_model()
    if model is None:
        return None
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(img).unsqueeze(0)
    with torch.no_grad():
        return float(torch.sigmoid(model(tensor)).item())


def _ml_prob_fruit(image_bytes: bytes):
    model = _load_fruit_model()
    if model is None:
        return None
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(img).unsqueeze(0)
    with torch.no_grad():
        return float(torch.sigmoid(model(tensor)).item())


def _combine_with_ml(
    crop_part: str,
    image_bytes: bytes,
    cv_ok: bool,
    cv_conf: float,
    cv_reason: Optional[str],
    threshold: float,
    ml_prob_fn,
):
    """
    CV is always a hard gate (except mode=off).
    MobileNet is optional secondary; never used to soft-accept CV failures.
    soft mode cannot bypass FRUIT/LEAF CV rejection.
    """
    mode = _gate_mode()
    reject_default = (
        REJECT_MESSAGE_FRUIT if crop_part == "FRUIT" else REJECT_MESSAGE
    )

    if mode == "off":
        try:
            Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return True, 1.0, None
        except Exception as e:
            return False, 0.0, f"Error: {str(e)}"

    if not cv_ok:
        return False, cv_conf, cv_reason or reject_default

    # CV passed — optional MobileNet secondary
    try:
        prob = ml_prob_fn(image_bytes)
    except Exception as e:
        return False, 0.0, f"Error: {str(e)}"

    if prob is None:
        return True, cv_conf, None

    ml_pass = prob > threshold
    confidence = prob if ml_pass else (1.0 - prob)

    if mode == "strict" and not ml_pass:
        return False, round(confidence, 4), reject_default

    # hybrid / soft: CV already passed; accept and report best confidence
    return True, round(max(cv_conf, prob if ml_pass else cv_conf), 4), None


def is_valid_leaf(image_bytes: bytes):
    """
    Returns: (is_valid, confidence, reason)
    LEAF cases only — tomato-leaf-like images.
    """
    cv_ok, cv_conf, cv_reason = is_valid_tomato_image(image_bytes, "LEAF")
    return _combine_with_ml(
        "LEAF",
        image_bytes,
        cv_ok,
        cv_conf,
        cv_reason,
        LEAF_GATE_THRESHOLD,
        _ml_prob_leaf,
    )


def is_valid_fruit(image_bytes: bytes):
    """
    Returns: (is_valid, confidence, reason)
    FRUIT cases only — tomato-fruit-like images.
    """
    cv_ok, cv_conf, cv_reason = is_valid_tomato_image(image_bytes, "FRUIT")
    return _combine_with_ml(
        "FRUIT",
        image_bytes,
        cv_ok,
        cv_conf,
        cv_reason,
        FRUIT_GATE_THRESHOLD,
        _ml_prob_fruit,
    )
