"""
U-Net predictors for leaf and fruit disease severity.

Leaf disease A/B checkpoints were trained as ResNet34 U-Net segmentation
models. Inference returns severity as the percent of pixels predicted as
diseased in the segmentation mask.
"""

import io
import os
from typing import Dict, Optional, Tuple

import segmentation_models_pytorch as smp
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(BASE_DIR, "ml", "models")

LEAF_MODEL_PATHS = {
    "A": os.path.join(MODEL_DIR, "unet_leaf_A.pth"),
    "B": os.path.join(MODEL_DIR, "unet_leaf_B.pth"),
}

FRUIT_MODEL_PATHS = {
    "A": os.path.join(MODEL_DIR, "unet_fruit_A.pth"),
    "B": os.path.join(MODEL_DIR, "unet_fruit_B.pth"),
}

IMAGE_SIZE = 224
MASK_THRESHOLD = 0.5
MIN_SEVERITY_PERCENT = 10.0
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_leaf_models: Dict[str, nn.Module] = {}
_fruit_models: Dict[str, nn.Module] = {}


_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def _load_leaf_model(disease: str) -> nn.Module:
    disease = disease.upper()
    if disease not in LEAF_MODEL_PATHS:
        raise ValueError("disease must be 'A' or 'B'")

    if disease in _leaf_models:
        return _leaf_models[disease]

    model_path = LEAF_MODEL_PATHS[disease]
    if not os.path.exists(model_path) or os.path.getsize(model_path) == 0:
        raise FileNotFoundError(f"U-Net leaf {disease} model not found at {model_path}")

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=1,
    ).to(DEVICE)
    state_dict = torch.load(model_path, map_location=DEVICE)
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    _leaf_models[disease] = model
    print(f"U-Net leaf {disease} model loaded successfully from {model_path}")
    return model


def _load_fruit_model(disease: str) -> nn.Module:
    disease = disease.upper()
    if disease not in FRUIT_MODEL_PATHS:
        raise ValueError("fruit disease must be 'A' or 'B'")

    if disease in _fruit_models:
        return _fruit_models[disease]

    model_path = FRUIT_MODEL_PATHS[disease]
    if not os.path.exists(model_path) or os.path.getsize(model_path) == 0:
        raise FileNotFoundError(f"U-Net fruit {disease} model not found at {model_path}")

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=1,
    ).to(DEVICE)
    state_dict = torch.load(model_path, map_location=DEVICE)
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    _fruit_models[disease] = model
    print(f"U-Net fruit {disease} model loaded successfully from {model_path}")
    return model


def _preprocess_image(image_bytes: bytes) -> torch.Tensor:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return _transform(image).unsqueeze(0).to(DEVICE)


def _mask_to_severity(mask_prob: torch.Tensor) -> Tuple[float, float]:
    mask_prob = mask_prob.squeeze()
    predicted_mask = mask_prob >= MASK_THRESHOLD

    severity = predicted_mask.float().mean().item() * 100

    if predicted_mask.any():
        confidence = mask_prob[predicted_mask].mean().item()
    else:
        confidence = (1.0 - mask_prob).mean().item()

    if severity < MIN_SEVERITY_PERCENT:
        print(
            f"U-Net low severity filtered: raw={severity:.2f}%, "
            f"threshold={MIN_SEVERITY_PERCENT}%"
        )
        return 0.0, round(confidence, 4)

    return round(severity, 2), round(confidence, 4)


def get_leaf_severity(image_bytes: bytes, disease: str):
    """
    disease = "A" or "B"
    Returns: (severity_percent, confidence)
    """
    try:
        model = _load_leaf_model(disease)
        tensor = _preprocess_image(image_bytes)

        with torch.no_grad():
            logits = model(tensor)
            mask_prob = torch.sigmoid(logits)

        return _mask_to_severity(mask_prob.cpu())
    except Exception as e:
        print(f"U-Net leaf {disease} prediction error: {e}")
        return 0.0, 0.0


def get_fruit_severity(image_bytes: bytes, disease: str):
    """
    disease = "A" or "B"
    Returns: (severity_percent, confidence)
    """
    try:
        model = _load_fruit_model(disease)
        tensor = _preprocess_image(image_bytes)

        with torch.no_grad():
            logits = model(tensor)
            mask_prob = torch.sigmoid(logits)

        return _mask_to_severity(mask_prob.cpu())
    except Exception as e:
        print(f"U-Net fruit {disease} prediction error: {e}")
        return 0.0, 0.0


# ── Multiclass Fruit UNet (fruit_multiclass_unet_A.pth) ──────────────────────

FRUIT_MULTICLASS_MODEL_PATH  = os.path.join(MODEL_DIR, "fruit_multiclass_unet_A.pth")
FRUIT_MULTICLASS_NUM_CLASSES = 5
FRUIT_MULTICLASS_IMAGE_SIZE  = 256   # from model metadata

# Class index → name  (matches metadata classes)
FRUIT_CLASS_NAMES = {
    0: "background",
    1: "anthracnose",
    2: "blossom_end_rot",
    3: "healthy_tomato",
    4: "spotted_wilt_virus",
}
FRUIT_DISEASE_CLASS_IDS = [1, 2, 4]  # excludes background (0) and healthy (3)
FRUIT_HEALTHY_CLASS_ID  = 3

_fruit_multiclass_model: Optional[nn.Module] = None

_multiclass_transform = transforms.Compose([
    transforms.Resize((FRUIT_MULTICLASS_IMAGE_SIZE, FRUIT_MULTICLASS_IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def _load_fruit_multiclass_model() -> nn.Module:
    global _fruit_multiclass_model
    if _fruit_multiclass_model is not None:
        return _fruit_multiclass_model

    if not os.path.exists(FRUIT_MULTICLASS_MODEL_PATH) or \
            os.path.getsize(FRUIT_MULTICLASS_MODEL_PATH) == 0:
        raise FileNotFoundError(
            f"Fruit multiclass U-Net not found at {FRUIT_MULTICLASS_MODEL_PATH}"
        )

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=FRUIT_MULTICLASS_NUM_CLASSES,
    ).to(DEVICE)
    state = torch.load(FRUIT_MULTICLASS_MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(state, strict=True)
    model.eval()

    _fruit_multiclass_model = model
    print(f"Fruit multiclass U-Net loaded from {FRUIT_MULTICLASS_MODEL_PATH}")
    return model


def get_fruit_multiclass_severity(image_bytes: bytes) -> dict:
    """
    Runs the 5-class fruit U-Net (fruit_multiclass_unet_A.pth).

    Severity formula (from model metadata):
        disease_pixels / (healthy_tomato_pixels + disease_pixels) * 100

    Returns:
        severity                  – overall disease %
        confidence                – mean predicted-class probability on disease pixels
        dominant_disease          – disease class with most pixels, or 'none'
        anthracnose_severity      – % relative to (healthy + all disease) pixels
        blossom_end_rot_severity  – same
        spotted_wilt_virus_severity – same
        healthy_percent           – healthy pixels / total pixels * 100
    """
    try:
        model  = _load_fruit_multiclass_model()
        image  = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = _multiclass_transform(image).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            logits    = model(tensor)                           # (1, 5, H, W)
            probs     = torch.softmax(logits, dim=1)           # (1, 5, H, W)
            pred_mask = torch.argmax(probs, dim=1).squeeze(0)  # (H, W)

        probs     = probs.squeeze(0).cpu()   # (5, H, W)
        pred_mask = pred_mask.cpu()          # (H, W)
        total_px  = pred_mask.numel()

        # Per-class pixel counts
        counts = {
            c: int((pred_mask == c).sum())
            for c in range(FRUIT_MULTICLASS_NUM_CLASSES)
        }

        healthy_px = counts[FRUIT_HEALTHY_CLASS_ID]
        disease_px = sum(counts[c] for c in FRUIT_DISEASE_CLASS_IDS)
        denom      = healthy_px + disease_px  # denominator per metadata formula

        def _sev(px: int) -> float:
            return round(px / denom * 100, 2) if denom > 0 else 0.0

        severity                    = _sev(disease_px)
        anthracnose_severity        = _sev(counts[1])
        blossom_end_rot_severity    = _sev(counts[2])
        spotted_wilt_virus_severity = _sev(counts[4])
        healthy_percent             = round(healthy_px / total_px * 100, 2)

        # Dominant disease
        disease_counts = {
            "anthracnose":        counts[1],
            "blossom_end_rot":    counts[2],
            "spotted_wilt_virus": counts[4],
        }
        dominant_disease = max(disease_counts, key=disease_counts.get)
        if disease_counts[dominant_disease] == 0:
            dominant_disease = "none"

        # Confidence: mean predicted-class probability across disease pixels
        max_probs    = probs.max(dim=0).values          # (H, W)
        disease_mask = torch.zeros_like(pred_mask, dtype=torch.bool)
        for c in FRUIT_DISEASE_CLASS_IDS:
            disease_mask |= (pred_mask == c)

        if disease_mask.any():
            confidence = round(max_probs[disease_mask].mean().item(), 4)
        else:
            confidence = round(max_probs.mean().item(), 4)

        print(
            f"[DEBUG] Fruit multiclass UNet: severity={severity}%, "
            f"dominant={dominant_disease}, healthy={healthy_percent}%, "
            f"confidence={confidence}"
        )

        return {
            "severity":                    severity,
            "confidence":                  confidence,
            "dominant_disease":            dominant_disease,
            "anthracnose_severity":        anthracnose_severity,
            "blossom_end_rot_severity":    blossom_end_rot_severity,
            "spotted_wilt_virus_severity": spotted_wilt_virus_severity,
            "healthy_percent":             healthy_percent,
        }

    except Exception as e:
        print(f"Fruit multiclass U-Net prediction error: {e}")
        return {
            "severity":                    0.0,
            "confidence":                  0.0,
            "dominant_disease":            "unknown",
            "anthracnose_severity":        0.0,
            "blossom_end_rot_severity":    0.0,
            "spotted_wilt_virus_severity": 0.0,
            "healthy_percent":             0.0,
        }
