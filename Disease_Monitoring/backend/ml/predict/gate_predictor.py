"""
Gate Predictor — MobileNetV2
Validates if uploaded image is a valid tomato leaf
"""

import os
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import io

# ── Path ─────────────────────────────────────────────
BASE_DIR   = os.path.abspath(
               os.path.join(os.path.dirname(__file__), "..", "..")
             )
LEAF_MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "gate_leaf.pth")
FRUIT_MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "gate_fruit.pth")

_leaf_model = None
_fruit_model = None

def _load_leaf_model():
    global _leaf_model
    if _leaf_model is not None:
        return _leaf_model

    if not os.path.exists(LEAF_MODEL_PATH):
        print(f"WARNING: gate_leaf.pth not found at {LEAF_MODEL_PATH}")
        return None

    # Must match EXACTLY what you used in Colab training
    model = models.mobilenet_v2(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.last_channel, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, 1)
    )
    model.load_state_dict(
        torch.load(LEAF_MODEL_PATH, map_location="cpu")
    )
    model.eval()
    _leaf_model = model
    print("Gate leaf model loaded successfully")
    return model

_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])

def _load_fruit_model():
    global _fruit_model
    if _fruit_model is not None:
        return _fruit_model

    if not os.path.exists(FRUIT_MODEL_PATH):
        print(f"WARNING: gate_fruit.pth not found at {FRUIT_MODEL_PATH}")
        return None

    # Same architecture as leaf model
    model = models.mobilenet_v2(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.last_channel, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, 1)
    )
    model.load_state_dict(
        torch.load(FRUIT_MODEL_PATH, map_location="cpu")
    )
    model.eval()
    _fruit_model = model
    print("Gate fruit model loaded successfully")
    return model

def is_valid_leaf(image_bytes: bytes):
    """
    Returns: (is_valid, confidence, reason)
    is_valid   = True (PASS) or False (REJECT)
    confidence = 0.0 to 1.0
    reason     = None if valid, message if rejected
    """
    model = _load_leaf_model()

    if model is None:
        # Placeholder if model file missing
        return True, 0.95, None

    try:
        img    = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = _transform(img).unsqueeze(0)

        with torch.no_grad():
            prob = torch.sigmoid(model(tensor)).item()

        is_valid   = prob > 0.5
        confidence = prob if is_valid else 1 - prob
        reason     = None if is_valid else \
                     "Image rejected: not a clear tomato leaf"

        return is_valid, round(confidence, 4), reason

    except Exception as e:
        return False, 0.0, f"Error: {str(e)}"

def is_valid_fruit(image_bytes: bytes):
    """
    Returns: (is_valid, confidence, reason)
    is_valid   = True (PASS) or False (REJECT)
    confidence = 0.0 to 1.0
    reason     = None if valid, message if rejected
    """
    model = _load_fruit_model()

    if model is None:
        # Placeholder if model file missing
        return True, 0.95, None

    try:
        img    = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = _transform(img).unsqueeze(0)

        with torch.no_grad():
            prob = torch.sigmoid(model(tensor)).item()

        is_valid   = prob > 0.5
        confidence = prob if is_valid else 1 - prob
        reason     = None if is_valid else \
                     "Image rejected: not a clear tomato fruit"

        return is_valid, round(confidence, 4), reason

    except Exception as e:
        return False, 0.0, f"Error: {str(e)}"