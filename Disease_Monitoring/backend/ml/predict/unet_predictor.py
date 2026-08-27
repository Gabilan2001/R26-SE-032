"""
Fruit disease severity U-Net predictor (legacy fruit pipeline support).

Leaf severity is handled by EfficientNet-B0 in severity/leaf/efficientnet_severity.py.
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

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class CustomUNet(nn.Module):
    """Placeholder wrapper for legacy fruit checkpoint loading."""

    def __init__(self):
        super().__init__()
        self.model_dict = None

    def forward(self, x):
        return x

    def load_from_checkpoint(self, state_dict):
        self.model_dict = state_dict
        for name, param in state_dict.items():
            if "weight" in name or "bias" in name:
                self.register_parameter(name.replace(".", "__"), nn.Parameter(param))
            else:
                self.register_buffer(name.replace(".", "__"), param)


FRUIT_MULTICLASS_MODEL_PATH = os.path.join(MODEL_DIR, "unet_severity_best.pth")
FRUIT_MULTICLASS_NUM_CLASSES = 5
FRUIT_MULTICLASS_IMAGE_SIZE = 256

FRUIT_CLASS_NAMES = {
    0: "background",
    1: "anthracnose",
    2: "blossom_end_rot",
    3: "healthy_tomato",
    4: "spotted_wilt_virus",
}
FRUIT_DISEASE_CLASS_IDS = [1, 2, 4]
FRUIT_HEALTHY_CLASS_ID = 3

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

    checkpoint = torch.load(FRUIT_MULTICLASS_MODEL_PATH, map_location=DEVICE)

    if isinstance(checkpoint, nn.Module):
        checkpoint.eval()
        _fruit_multiclass_model = checkpoint
        return checkpoint

    if isinstance(checkpoint, dict):
        model = smp.Unet(
            encoder_name="resnet34",
            encoder_weights=None,
            in_channels=3,
            classes=FRUIT_MULTICLASS_NUM_CLASSES,
        ).to(DEVICE)
        model.load_state_dict(checkpoint, strict=False)
        model.eval()
        _fruit_multiclass_model = model
        return model

    raise RuntimeError(
        f"Could not load model from {FRUIT_MULTICLASS_MODEL_PATH}. "
        f"Expected nn.Module or compatible state_dict, got {type(checkpoint)}"
    )


def _detect_dominant_disease(image_pil: Image.Image, disease_mask: torch.Tensor) -> Tuple[str, Dict[str, float]]:
    import cv2
    import numpy as np

    try:
        mask_np = disease_mask.cpu().numpy().astype(np.uint8) * 255
        image_np = np.array(image_pil)
        result = cv2.findContours(mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = result[-2] if len(result) == 3 else result[0]

        if not contours:
            return "anthracnose", {
                "anthracnose": 0.33,
                "blossom_end_rot": 0.33,
                "spotted_wilt_virus": 0.34,
            }

        lesion_sizes = []
        lesion_positions = []
        lesion_colors = []
        h, w = mask_np.shape
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50:
                lesion_sizes.append(area)
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    lesion_positions.append((cx, cy, cy / h))
                    if cy < len(image_np) and cx < len(image_np[0]):
                        lesion_colors.append(image_np[cy, cx])

        if not lesion_sizes:
            return "anthracnose", {
                "anthracnose": 0.33,
                "blossom_end_rot": 0.33,
                "spotted_wilt_virus": 0.34,
            }

        avg_lesion_size = np.mean(lesion_sizes)
        lesion_count = len(lesion_sizes)
        vertical_positions = [p[2] for p in lesion_positions]
        bottom_concentration = (
            sum(1 for p in vertical_positions if p > 0.7) / len(vertical_positions)
            if vertical_positions else 0
        )

        if lesion_colors:
            colors_array = np.array(lesion_colors)
            avg_red = np.mean(colors_array[:, 0]) if len(colors_array) > 0 else 0
            avg_green = np.mean(colors_array[:, 1]) if len(colors_array) > 0 else 0
            avg_blue = np.mean(colors_array[:, 2]) if len(colors_array) > 0 else 0
            darkness = avg_red > max(avg_green, avg_blue) * 1.2
        else:
            darkness = False

        anthracnose_score = 0.0
        blossom_end_rot_score = 0.0
        spotted_wilt_virus_score = 0.0

        if avg_lesion_size < 500 and lesion_count > 3:
            anthracnose_score += 0.4
        if darkness:
            anthracnose_score += 0.3
        if avg_lesion_size > 800 or lesion_count <= 2:
            blossom_end_rot_score += 0.3
        if bottom_concentration > 0.5:
            blossom_end_rot_score += 0.4
        if 3 < lesion_count <= 20 and avg_lesion_size < 1000:
            spotted_wilt_virus_score += 0.35
        if bottom_concentration < 0.3 and 0.3 < np.var(vertical_positions):
            spotted_wilt_virus_score += 0.25

        total_score = anthracnose_score + blossom_end_rot_score + spotted_wilt_virus_score
        if total_score == 0:
            anthracnose_score = blossom_end_rot_score = spotted_wilt_virus_score = 1.0
            total_score = 3.0

        disease_scores = {
            "anthracnose": anthracnose_score / total_score,
            "blossom_end_rot": blossom_end_rot_score / total_score,
            "spotted_wilt_virus": spotted_wilt_virus_score / total_score,
        }
        dominant = max(disease_scores, key=disease_scores.get)
        return dominant, disease_scores

    except Exception as e:
        print(f"[WARNING] Disease detection error: {e}. Using default distribution.")
        return "anthracnose", {
            "anthracnose": 0.33,
            "blossom_end_rot": 0.33,
            "spotted_wilt_virus": 0.34,
        }


def get_fruit_multiclass_severity(image_bytes: bytes) -> dict:
    """Runs the multiclass fruit disease U-Net (unet_severity_best.pth)."""
    try:
        model = _load_fruit_multiclass_model()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = _multiclass_transform(image).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            output = model(tensor)
            probs = torch.softmax(output, dim=1)
            preds = torch.argmax(probs, dim=1).cpu()
            flat_preds = preds.flatten()
            counts = torch.bincount(flat_preds, minlength=FRUIT_MULTICLASS_NUM_CLASSES)

            anth_pixels = counts[1].item()
            ber_pixels = counts[2].item()
            heal_pixels = counts[3].item()
            swv_pixels = counts[4].item()
            total_fruit_pixels = anth_pixels + ber_pixels + heal_pixels + swv_pixels

            if total_fruit_pixels == 0:
                return {
                    "severity": "LOW",
                    "confidence": 0.0,
                    "dominant_disease": "none",
                    "anthracnose_severity": 0.0,
                    "blossom_end_rot_severity": 0.0,
                    "spotted_wilt_virus_severity": 0.0,
                    "healthy_percent": 100.0,
                }

            anth_pct = round((anth_pixels / total_fruit_pixels) * 100, 2)
            ber_pct = round((ber_pixels / total_fruit_pixels) * 100, 2)
            swv_pct = round((swv_pixels / total_fruit_pixels) * 100, 2)
            heal_pct = round((heal_pixels / total_fruit_pixels) * 100, 2)
            total_disease_pct = anth_pct + ber_pct + swv_pct

            disease_scores = {
                "anthracnose": anth_pct,
                "blossom_end_rot": ber_pct,
                "spotted_wilt_virus": swv_pct,
            }
            dominant_disease = (
                max(disease_scores, key=disease_scores.get) if total_disease_pct > 0 else "none"
            )

            disease_mask = (preds > 0) & (preds != 3)
            if disease_mask.any():
                confidence = probs[0].cpu().gather(0, preds)[disease_mask].mean().item()
            else:
                confidence = probs[0, 3].cpu().mean().item()

            if total_disease_pct < 20:
                severity_level = "LOW"
            elif total_disease_pct < 50:
                severity_level = "MEDIUM"
            else:
                severity_level = "HIGH"

        return {
            "severity": severity_level,
            "confidence": round(confidence, 4),
            "dominant_disease": dominant_disease,
            "anthracnose_severity": anth_pct,
            "blossom_end_rot_severity": ber_pct,
            "spotted_wilt_virus_severity": swv_pct,
            "healthy_percent": heal_pct,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "severity": "UNKNOWN",
            "confidence": 0.0,
            "dominant_disease": "unknown",
            "anthracnose_severity": 0.0,
            "blossom_end_rot_severity": 0.0,
            "spotted_wilt_virus_severity": 0.0,
            "healthy_percent": 0.0,
        }
