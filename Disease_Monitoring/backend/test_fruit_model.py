"""
Quick sanity check for fruit_multiclass_unet_A.pth
Run from: d:\Research\RP-COM-MY\Monitoring
    python test_fruit_model.py
"""
import os, sys, io
import torch
import segmentation_models_pytorch as smp
from PIL import Image

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "fruit_multiclass_unet_A.pth")

NUM_CLASSES = 5
IMAGE_SIZE  = 256
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CLASS_NAMES = {
    0: "background",
    1: "anthracnose",
    2: "blossom_end_rot",
    3: "healthy_tomato",
    4: "spotted_wilt_virus",
}
DISEASE_IDS = [1, 2, 4]
HEALTHY_ID  = 3

print("=" * 60)
print("Fruit Multiclass U-Net — Connection Check")
print("=" * 60)

# ── 1. File check ──────────────────────────────────────────────
if not os.path.exists(MODEL_PATH):
    print(f"[FAIL] Model file NOT found:\n       {MODEL_PATH}")
    sys.exit(1)

size_mb = os.path.getsize(MODEL_PATH) / 1024 / 1024
print(f"[OK]   Model file found  ({size_mb:.1f} MB)")
print(f"       Path: {MODEL_PATH}")

# ── 2. Load model ──────────────────────────────────────────────
print("\n[...] Loading model architecture (ResNet34 UNet, 5 classes) ...")
try:
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=NUM_CLASSES,
    ).to(DEVICE)
    state = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(state, strict=True)
    model.eval()
    print(f"[OK]   Model loaded on {DEVICE}")
except Exception as e:
    print(f"[FAIL] Could not load model: {e}")
    sys.exit(1)

# ── 3. Dummy forward pass ──────────────────────────────────────
print("\n[...] Running dummy forward pass (256×256 random image) ...")
try:
    dummy = torch.rand(1, 3, IMAGE_SIZE, IMAGE_SIZE).to(DEVICE)
    with torch.no_grad():
        logits    = model(dummy)                          # (1, 5, H, W)
        probs     = torch.softmax(logits, dim=1)          # (1, 5, H, W)
        pred_mask = torch.argmax(probs, dim=1).squeeze(0) # (H, W)

    print(f"[OK]   Output shape : {list(logits.shape)}")
    print(f"[OK]   Prob range   : [{probs.min().item():.4f}, {probs.max().item():.4f}]")

    # Class distribution on dummy image
    probs_cpu     = probs.squeeze(0).cpu()
    pred_mask_cpu = pred_mask.cpu()
    total_px      = pred_mask_cpu.numel()
    counts = {c: int((pred_mask_cpu == c).sum()) for c in range(NUM_CLASSES)}

    print("\n  Pixel distribution (random noise image — values only for shape check):")
    for cls_id, name in CLASS_NAMES.items():
        pct = counts[cls_id] / total_px * 100
        print(f"    class {cls_id} [{name:<22}]: {counts[cls_id]:6d} px  ({pct:.1f}%)")

    # Severity formula check
    healthy_px  = counts[HEALTHY_ID]
    disease_px  = sum(counts[c] for c in DISEASE_IDS)
    denom       = healthy_px + disease_px
    severity    = round(disease_px / denom * 100, 2) if denom > 0 else 0.0
    print(f"\n  Severity formula result: {severity}%  (random noise — not meaningful)")

except Exception as e:
    print(f"[FAIL] Forward pass error: {e}")
    sys.exit(1)

# ── 4. Predictor function check ────────────────────────────────
print("\n[...] Testing get_fruit_multiclass_severity() from unet_predictor ...")
try:
    # Create a synthetic 300×300 RGB image
    img = Image.new("RGB", (300, 300), color=(180, 90, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    sys.path.insert(0, BASE_DIR)
    from ml.predict.unet_predictor import get_fruit_multiclass_severity
    result = get_fruit_multiclass_severity(img_bytes)

    print("[OK]   Predictor returned:")
    for k, v in result.items():
        print(f"         {k:<30} = {v}")

except Exception as e:
    print(f"[FAIL] Predictor error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL CHECKS PASSED — Model is connected correctly.")
print("=" * 60)
