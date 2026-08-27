"""
app.py
======
Flask backend for TomatoScan Disease Detection System
Supports multiple model switching via API
Background removal applied before YOLO inference

Run from:
  C:\\Users\\mfart\\Desktop\\Research\\Disease Detection\\R26-SE-032\\Disease_Detection\\pipeline\\stage4_inference\\
  python app.py

Then open: http://localhost:5000
"""

import base64
from pathlib import Path

import cv2
import numpy as np
import torch
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from ultralytics import YOLO
from PIL import Image
from rembg import remove as rembg_remove

# ── RAG Treatment System ──────────────────────────────────────────────────────
try:
    from rag import query_rag
    RAG_AVAILABLE = True
except Exception as e:
    RAG_AVAILABLE = False
    print(f"  RAG unavailable: {e}")

# ── Leaf Validator ────────────────────────────────────────────────────────────
from torchvision import models, transforms
import torch.nn as nn

BASE = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
VALIDATOR_PATH = BASE / "models" / "leaf_validator.pth"
VALIDATOR_THRESHOLD = 0.75

def load_leaf_validator():
    ckpt = torch.load(str(VALIDATOR_PATH), map_location="cpu", weights_only=False)
    m    = models.efficientnet_b0(weights=None)
    m.classifier[1] = nn.Linear(m.classifier[1].in_features, 2)
    m.load_state_dict(ckpt["model_state_dict"])
    m.eval().to("cuda" if torch.cuda.is_available() else "cpu")
    return m

def is_tomato_leaf(img_bgr, validator_model):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])
    from PIL import Image as PILImage
    pil = PILImage.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    t   = transform(pil).unsqueeze(0).to("cuda" if torch.cuda.is_available() else "cpu")
    with torch.no_grad():
        probs = torch.softmax(validator_model(t), dim=1)[0].cpu().numpy()
    tomato_conf = float(probs[0])
    return tomato_conf >= VALIDATOR_THRESHOLD, round(tomato_conf, 4)

# ── Model Registry ────────────────────────────────────────────────────────────

MODELS = {
    "yolov8s_2class": {
        "label"   : "YOLOv8s",
        "path"    : BASE / "models" / "yolov8s" / "best_2class.pt",
        "classes" : ["Early_Blight", "Late_Blight"],
        "map"     : "63%",
        "arch"    : "YOLOv8s",
    },
    "yolov8m_clean": {
        "label"   : "YOLOv8m",
        "path"    : BASE / "models" / "yolov8m" / "best_clean.pt",
        "classes" : ["Early_Blight", "Late_Blight"],
        "map"     : "70%",
        "arch"    : "YOLOv8m",
    },
    "yolov8m_hybrid4class": {
        "label"   : "YOLOv8m (4-class Hybrid)",
        "path"    : BASE / "models" / "yolov8m_hybrid4class" / "best.pt",
        "classes" : ["Early_Blight", "Late_Blight", "Healthy", "Leaf_Miner"],
        "map"     : "78%",  # mAP50-95 on held-out test set (mAP50 92%)
        "arch"    : "YOLOv8m",
    },
    "yolov8m_downsampled640": {
        "label"   : "YOLOv8m (4-class, downsampled-640)",
        "path"    : BASE / "models" / "yolov8m_downsampled640" / "best.pt",
        "classes" : ["Early_Blight", "Late_Blight", "Healthy", "Leaf_Miner"],
        "map"     : "47%",  # mAP50-95 on held-out test set (mAP50 72%)
        "arch"    : "YOLOv8m",
    },
    "yolov8m_native640": {
        "label"   : "YOLOv8m (4-class, native-640)",
        "path"    : BASE / "models" / "yolov8m_native640" / "best.pt",
        "classes" : ["Early_Blight", "Late_Blight", "Healthy", "Leaf_Miner"],
        "map"     : "48%",  # mAP50-95 on held-out test set (mAP50 73%)
        "arch"    : "YOLOv8m",
    },
}

CLASS_COLORS_BGR = {
    "Early_Blight"      : (50,  100, 255),
    "Late_Blight"       : (255, 180,  50),
    "Healthy"           : (60,  200,  60),
    "Leaf_Miner"        : (0,   165, 255),
}

CONF_THRESHOLD = 0.30
IOU_THRESHOLD  = 0.45

# ── App setup ─────────────────────────────────────────────────────────────────
FRONTEND = BASE / "frontend"
app      = Flask(__name__, static_folder=str(FRONTEND))
CORS(app)

device = "0" if torch.cuda.is_available() else "cpu"

loaded_models = {}

def get_model(model_key):
    if model_key not in loaded_models:
        cfg  = MODELS[model_key]
        print(f"Loading {cfg['label']}...")
        loaded_models[model_key] = YOLO(str(cfg["path"]))
        print(f"  Loaded ✅")
    return loaded_models[model_key]

print("=" * 55)
print("TomatoScan — Multi-Model Detection Server")
print("=" * 55)
print(f"  Device : {'CUDA (RTX 4060)' if device == '0' else 'CPU'}")
get_model("yolov8m_clean")
print("  Loading leaf validator...")
leaf_validator = load_leaf_validator()
print("  Leaf validator loaded ✅")
print(f"  Ready  : http://localhost:5000")
print("=" * 55)


# ── Helpers ───────────────────────────────────────────────────────────────────
def remove_background(img_bgr):
    """
    Remove background from BGR image.
    Returns clean BGR image with white background.
    Falls back to original if removal fails.
    """
    try:
        pil_img   = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        pil_no_bg = rembg_remove(pil_img)
        # Paste onto white background
        bg = Image.new("RGBA", pil_no_bg.size, (255, 255, 255, 255))
        bg.paste(pil_no_bg, mask=pil_no_bg.split()[3])
        clean_bgr = cv2.cvtColor(np.array(bg.convert("RGB")), cv2.COLOR_RGB2BGR)
        return clean_bgr
    except Exception as e:
        print(f"  BG removal failed: {e} — using original")
        return img_bgr


def draw_detections(img, detections):
    out = img.copy()
    for det in detections:
        name  = det["class_name"]
        conf  = det["confidence"]
        x1, y1, x2, y2 = det["x1"], det["y1"], det["x2"], det["y2"]
        color = CLASS_COLORS_BGR.get(name, (200, 200, 200))
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"{name.replace('_', ' ')} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(out, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
        cv2.putText(out, label, (x1 + 3, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return out


def encode_image(img):
    _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return base64.b64encode(buffer).decode("utf-8")

def get_treatment(diseases_found):
    if not RAG_AVAILABLE or not diseases_found:
        return None
    try:
        # Healthy has no treatment to look up; only query for actual disease/pest classes
        treatable = [d for d in diseases_found if d != "Healthy"]
        if not treatable:
            return None

        readable = [d.replace("_", " ") for d in treatable]
        if len(readable) == 1:
            query = (
                f"What treatment and dosage for {readable[0]} on tomato, "
                f"including how much to use for one plant"
            )
        else:
            disease_phrase = ", ".join(readable[:-1]) + " and " + readable[-1]
            query = (
                f"These were detected together on the same tomato plant: {disease_phrase}. "
                f"Give a separate complete treatment (including dosage and how much for one plant) "
                f"for EACH one, then explain whether any of these can be treated together with "
                f"fewer sprays or need to stay separate."
            )
        result = query_rag(query, diseases=treatable)
        return {"answer": result["answer"], "sources": result["sources"]}
    except Exception as e:
        print(f"  RAG query failed: {e}")
        return None
    
# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(str(FRONTEND), "index.html")


@app.route("/models", methods=["GET"])
def list_models():
    return jsonify({
        key: {
            "label"  : v["label"],
            "map"    : v["map"],
            "arch"   : v["arch"],
            "classes": v["classes"],
        }
        for key, v in MODELS.items()
    })


@app.route("/predict", methods=["POST"])
def predict():
    model_key = request.form.get("model", "yolov8m_clean")

    if model_key not in MODELS:
        return jsonify({"error": f"Unknown model: {model_key}"}), 400

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    cfg         = MODELS[model_key]
    class_names = cfg["classes"]

    file_bytes   = np.frombuffer(request.files["image"].read(), np.uint8)
    original_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if original_img is None:
        return jsonify({"error": "Could not decode image"}), 400

    # Blank image check
    if float(np.std(cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY))) < 10:
        return jsonify({
            "error"         : "Image appears blank or invalid",
            "valid"         : False,
            "detections"    : [],
            "diseases_found": [],
            "co_occurrence" : False,
            "total_boxes"   : 0,
            "annotated_image": encode_image(original_img),
        })
    
    # ── Leaf validation ───────────────────────────────────────────────────────────
    valid_leaf, leaf_conf = is_tomato_leaf(original_img, leaf_validator)
    if not valid_leaf:
        return jsonify({
            "error"         : f"Not a tomato leaf image (confidence: {leaf_conf:.0%}). Please upload a clear tomato leaf photo.",
            "valid"         : False,
            "leaf_conf"     : leaf_conf,
            "detections"    : [],
            "diseases_found": [],
            "co_occurrence" : False,
            "total_boxes"   : 0,
            "annotated_image": encode_image(original_img),
        })
    
    print(f"  Leaf validated ✅ (confidence: {leaf_conf:.2f})")

    # ── Remove background — YOLO runs on clean image ──────────────────────────
    print("  Removing background...")
    clean_img = remove_background(original_img)
    print("  Background removed ✅")

    # ── Run YOLO on clean image ───────────────────────────────────────────────
    model   = get_model(model_key)
    results = model.predict(
        clean_img,
        conf    = CONF_THRESHOLD,
        iou     = IOU_THRESHOLD,
        device  = device,
        verbose = False,
    )

    h, w = original_img.shape[:2]
    detections = []
    for r in results:
        if r.boxes is None:
            continue
        for box in r.boxes:
            cls_idx = int(box.cls.item())
            conf    = float(box.conf.item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            name = class_names[cls_idx] if cls_idx < len(class_names) else f"class_{cls_idx}"
            detections.append({
                "class_name": name,
                "class_idx" : cls_idx,
                "confidence": round(conf, 4),
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "box_area"  : round((x2-x1)*(y2-y1)/(w*h), 4),
            })

    if len(detections) == 0:
        return jsonify({
            "error"         : "No disease detected — ensure image shows a tomato leaf with visible symptoms",
            "valid"         : False,
            "detections"    : [],
            "diseases_found": [],
            "co_occurrence" : False,
            "total_boxes"   : 0,
            "annotated_image": encode_image(original_img),
        })

    high_conf = [d for d in detections if d["confidence"] >= 0.35]
    if len(high_conf) == 0:
        return jsonify({
            "error"         : "Low confidence detections — please upload a clearer image",
            "valid"         : False,
            "detections"    : detections,
            "diseases_found": [],
            "co_occurrence" : False,
            "total_boxes"   : len(detections),
            "annotated_image": encode_image(draw_detections(original_img, detections)),
        })

    diseases_found = sorted(set(d["class_name"] for d in detections))
    co_occurrence  = len(diseases_found) >= 2

    # ── Draw boxes on ORIGINAL image — user sees real image with boxes ────────
    annotated = draw_detections(original_img, detections)

     # ── RAG treatment ─────────────────────────────────────────────────────────
    treatment = get_treatment(diseases_found)

    return jsonify({
        "valid"          : True,
        "detections"     : detections,
        "diseases_found" : diseases_found,
        "co_occurrence"  : co_occurrence,
        "total_boxes"    : len(detections),
        "annotated_image": encode_image(annotated),
        "treatment"      : treatment,
        "model_info"     : {
            "key"      : model_key,
            "label"    : cfg["label"],
            "classes"  : class_names,
            "map"      : cfg["map"],
            "arch"     : cfg["arch"],
            "conf_thr" : CONF_THRESHOLD,
            "iou_thr"  : IOU_THRESHOLD,
            "device"   : "CUDA (RTX 4060)" if torch.cuda.is_available() else "CPU",
        }
    })


@app.route("/health")
def health():
    return jsonify({
        "status" : "ok",
        "device" : "CUDA" if torch.cuda.is_available() else "CPU",
        "models" : list(MODELS.keys()),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
