"""
Leaf severity adapter.

Primary severity = OpenCV estimated affected-area % (no retrain):
  severity_score = percentage / 100
  severity_class = HIGH if percentage > 30% else LOW

EfficientNet-B0 is preserved for:
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

from config.observation_config import LEAF_SEVERITY_MODEL_PATH
from severity.cv_area_severity import estimate_affected_area

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model: Optional[nn.Module] = None

_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class ModelNotConfiguredError(RuntimeError):
    pass


def _load_model() -> nn.Module:
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(LEAF_SEVERITY_MODEL_PATH):
        raise ModelNotConfiguredError(
            f"Leaf severity model not found at {LEAF_SEVERITY_MODEL_PATH}"
        )

    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, 2)
    state_dict = torch.load(LEAF_SEVERITY_MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict, strict=True)
    model.to(DEVICE)
    model.eval()
    _model = model
    return model


def _extract_features(model: nn.Module, tensor: torch.Tensor) -> torch.Tensor:
    x = model.features(tensor)
    x = model.avgpool(x)
    return torch.flatten(x, 1)


def predict_leaf_severity(image_bytes: bytes) -> Dict:
    """
    Automatic leaf severity from visual affected-area estimate + CNN embedding.

    severity_score = estimated_affected_area_percentage / 100  (0–1)
    severity_class = LOW | HIGH  (>30% → HIGH)
    embedding = 1280-d CNN features for consistency
    cnn_high_prob = secondary EfficientNet P(HIGH)
    """
    model = _load_model()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        features = _extract_features(model, tensor)
        logits = model.classifier(features)
        probs = torch.softmax(logits, dim=1).squeeze(0)
        high_prob = float(probs[1].item())
        embedding: List[float] = features.squeeze(0).cpu().tolist()

    area = estimate_affected_area(image_bytes, "LEAF")
    return {
        "severity_score": area["severity_score"],
        "severity_class": area["severity_class"],
        "estimated_affected_area_percentage": area["estimated_affected_area_percentage"],
        "cnn_high_prob": round(high_prob, 4),
        "embedding": embedding,
    }


def is_leaf_model_available() -> bool:
    return os.path.exists(LEAF_SEVERITY_MODEL_PATH)
