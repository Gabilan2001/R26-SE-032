"""
Quick sanity check for unet_severity_best.pth
Run from: d:\Research\RP-COM-MY\Monitoring
    python test_fruit_model.py
"""
import os, sys, io
import torch
from PIL import Image

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "unet_severity_best.pth")

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
print("\n[...] Loading model from unet_severity_best.pth ...")

try:
    model = torch.load(MODEL_PATH, map_location=DEVICE)
    
    if not isinstance(model, torch.nn.Module):
        print(f"[FAIL] Model is not a nn.Module, got {type(model)}")
        sys.exit(1)
    
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
        output = model(dummy)

    print(f"[OK]   Model produced output")
    
    # Try to extract severity information
    if hasattr(output, 'shape'):
        print(f"[OK]   Output shape : {list(output.shape)}")
    
    print("\n[OK]   Forward pass successful")

except Exception as e:
    print(f"[FAIL] Forward pass error: {e}")
    import traceback
    traceback.print_exc()
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
