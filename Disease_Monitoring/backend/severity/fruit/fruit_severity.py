"""
Fruit severity adapter.

Primary severity = OpenCV estimated affected-area % (no retrain):
  severity_score = percentage / 100
  severity_class = HIGH if percentage > 30% else LOW

Fruit EfficientNet is preserved for:
  - 1280-d embedding (visual consistency)
  - cnn_high_prob secondary signal
"""

import io
import os
from typing import Dict, List, Optional

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

from config.observation_config import FRUIT_SEVERITY_MODEL_PATH
from severity.cv_area_severity import estimate_affected_area

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model: Optional[nn.Module] = None

_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class FruitModelNotConfiguredError(RuntimeError):
    """Raised when the Fruit CNN severity model has not been configured yet."""


def _load_model() -> nn.Module:
    global _model
    if _model is not None:
        return _model

    if not FRUIT_SEVERITY_MODEL_PATH or not os.path.exists(FRUIT_SEVERITY_MODEL_PATH):
        raise FruitModelNotConfiguredError(
            "Fruit severity CNN is not configured. Set FRUIT_SEVERITY_MODEL_PATH to the "
            "updated Fruit EfficientNet checkpoint when available."
        )

    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, 2)
    state_dict = torch.load(FRUIT_SEVERITY_MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict, strict=True)
    model.to(DEVICE)
    model.eval()
    _model = model
    return model


def _extract_features(model: nn.Module, tensor: torch.Tensor) -> torch.Tensor:
    x = model.features(tensor)
    x = model.avgpool(x)
    return torch.flatten(x, 1)


def predict_fruit_severity(image_bytes: bytes) -> Dict:
    """Automatic fruit severity from visual affected-area estimate + CNN embedding."""
    model = _load_model()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        features = _extract_features(model, tensor)
        logits = model.classifier(features)
        probs = torch.softmax(logits, dim=1).squeeze(0)
        high_prob = float(probs[1].item())
        embedding: List[float] = features.squeeze(0).cpu().tolist()

    area = estimate_affected_area(image_bytes, "FRUIT")
    return {
        "severity_score": area["severity_score"],
        "severity_class": area["severity_class"],
        "estimated_affected_area_percentage": area["estimated_affected_area_percentage"],
        "cnn_high_prob": round(high_prob, 4),
        "embedding": embedding,
    }


def is_fruit_model_available() -> bool:
    return bool(FRUIT_SEVERITY_MODEL_PATH) and os.path.exists(FRUIT_SEVERITY_MODEL_PATH)
