"""
Comprehensive test for Leaf Monitoring Pipeline:
1. Gate Model (gate_leaf.pth)
2. U-Net Models (unet_leaf_A.pth, unet_leaf_B.pth)
3. Weather Utility
4. Full Leaf Service Upload Logic
"""
import os, sys, io, asyncio
import torch
from PIL import Image

# Add current dir to path
sys.path.append(os.getcwd())

from ml.predict.gate_predictor import is_valid_leaf
from ml.predict.unet_predictor import get_leaf_severity
from utils.weather_utils import get_weather_risk
from services import leaf_service

print("="*60)
print("LEAF SYSTEM CONNECTION CHECK")
print("="*60)

def test_models():
    print("\n[1/4] Checking Model Files & Loading...")
    models_dir = "ml/models"
    files = ["gate_leaf.pth", "unet_leaf_A.pth", "unet_leaf_B.pth"]
    
    for f in files:
        path = os.path.join(models_dir, f)
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024 / 1024
            print(f"  [OK] Found {f} ({size:.1f} MB)")
        else:
            print(f"  [!!] Missing {f} at {path}")

def test_inference():
    print("\n[2/4] Testing Model Inference (Dummy Data)...")
    # Create dummy image
    img = Image.new('RGB', (224, 224), color=(73, 109, 137))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    # Gate check
    valid, conf, reason = is_valid_leaf(img_bytes)
    print(f"  Gate Check: valid={valid}, confidence={conf}, reason={reason}")

    # UNet Severity
    sev_a, conf_a = get_leaf_severity(img_bytes, "A")
    sev_b, conf_b = get_leaf_severity(img_bytes, "B")
    print(f"  UNet A Severity: {sev_a}%, confidence: {conf_a}")
    print(f"  UNet B Severity: {sev_b}%, confidence: {conf_b}")

def test_weather():
    print("\n[3/4] Testing Weather API Utility...")
    # Test with a known location (Colombo, Sri Lanka approx)
    lat, lon = 6.9271, 79.8612
    risk = get_weather_risk(lat, lon)
    print(f"  City: {risk.get('city')}")
    print(f"  Risk Score: {risk.get('risk_score')}")
    print(f"  Risk Level: {risk.get('risk_level')}")
    print(f"  Alert: {risk.get('alert')}")

async def test_full_service():
    print("\n[4/4] Testing Full Leaf Service Pipeline...")
    # Create dummy image
    img = Image.new('RGB', (224, 224), color=(73, 109, 137))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    # Mock UploadFile
    class MockFile:
        async def read(self): return img_bytes
    
    try:
        response = await leaf_service.process_upload(
            file=MockFile(),
            session_id="test_session_123",
            day=1,
            lat=6.9271,
            lon=79.8612
        )
        print("  Service Response:")
        for k, v in response.items():
            if k != "weather_details": # skip details for brevity
                print(f"    {k}: {v}")
    except Exception as e:
        print(f"  [ERROR] Service pipeline failed: {e}")

if __name__ == "__main__":
    test_models()
    test_inference()
    test_weather()
    asyncio.run(test_full_service())
    print("\n" + "="*60)
    print("LEAF SYSTEM TEST COMPLETE")
    print("="*60)
