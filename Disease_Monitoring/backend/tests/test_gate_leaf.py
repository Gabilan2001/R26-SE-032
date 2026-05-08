"""
Test Gate Model on individual images
Shows PASS / REJECT with confidence
"""

import os
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image

BASE_DIR   = os.path.abspath(
               os.path.join(os.path.dirname(__file__), "..", "..")
             )
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "gate_leaf.pth")


def load_model():
    model = models.mobilenet_v2(pretrained=False)
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.5),
        nn.Linear(model.last_channel, 256),
        nn.ReLU(),
        nn.Dropout(p=0.3),
        nn.Linear(256, 1)
    )
    model.load_state_dict(
        torch.load(MODEL_PATH, map_location="cpu")
    )
    model.eval()
    return model


def predict(image_path, model):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225]
        )
    ])
    img    = Image.open(image_path).convert("RGB")
    tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        prob = torch.sigmoid(model(tensor)).item()

    is_pass    = prob > 0.5
    confidence = prob if is_pass else 1 - prob
    result     = "✅ PASS"   if is_pass else "❌ REJECT"
    reason     = "Valid tomato leaf" if is_pass else "Not a valid tomato leaf"

    return {
        "result":     result,
        "confidence": round(confidence * 100, 2),
        "reason":     reason,
        "raw_prob":   round(prob, 4)
    }


def run_tests():
    print("=" * 55)
    print("  Gate Model Test")
    print("=" * 55)

    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found at {MODEL_PATH}")
        print("Run training first.")
        return

    model = load_model()
    print(f"Model loaded from: {MODEL_PATH}\n")

    # Find test images
    img_root = os.path.join(BASE_DIR, "datasets", "leaf_disease")
    test_cases = []

    for folder in os.listdir(img_root):
        folder_path = os.path.join(img_root, folder)
        if not os.path.isdir(folder_path):
            continue
        if folder == "REJECT":
            continue
        imgs = [f for f in os.listdir(folder_path)
                if f.lower().endswith(('.jpg','.jpeg','.png'))]
        if imgs:
            test_cases.append({
                "path":     os.path.join(folder_path, imgs[0]),
                "expected": "✅ PASS",
                "desc":     folder[:30]
            })
        if len(test_cases) >= 5:
            break

    # Add a reject sample
    reject_path = os.path.join(img_root, "REJECT")
    if os.path.exists(reject_path):
        rejects = os.listdir(reject_path)
        if rejects:
            test_cases.append({
                "path":     os.path.join(reject_path, rejects[0]),
                "expected": "❌ REJECT",
                "desc":     "Bad quality image"
            })

    print(f"{'#':<4} {'Description':<32} {'Expected':<12} "
          f"{'Result':<12} {'Confidence':<12} {'Status'}")
    print("-" * 80)

    passed = 0
    for i, tc in enumerate(test_cases):
        out    = predict(tc["path"], model)
        status = "✓" if out["result"] == tc["expected"] else "✗"
        if status == "✓":
            passed += 1
        print(f"{i+1:<4} {tc['desc']:<32} {tc['expected']:<12} "
              f"{out['result']:<12} {out['confidence']}%{'':<5} {status}")

    print("-" * 80)
    print(f"Passed: {passed}/{len(test_cases)}")


if __name__ == "__main__":
    run_tests()