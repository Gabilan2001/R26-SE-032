"""
app.py
======
Flask backend for TomatoScan Disease Detection System
Supports multiple model switching via API

Run from:
  C:\\Users\\mfart\\Desktop\\Research\\Disease Detection\\pipeline\\stage4_inference\\
  python app.py

Then open: http://localhost:5000
"""

import base64
from pathlib import Path

import cv2
import numpy as np
import torch
from flask import Flask, request, jsonify, send_from_directory
from ultralytics import YOLO

# ── Model Registry ────────────────────────────────────────────────────────────
BASE = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection")

MODELS = {
    "yolov8s_3class": {
        "label"   : "YOLOv8s — 3 Class",
        "desc"    : "Early Blight + Late Blight + Septoria",
        "path"    : BASE / "models" / "yolov8s" / "best_3class.pt",
        "classes" : ["Early_Blight", "Late_Blight", "Septoria_Leaf_Spot"],
        "map"     : "0.667",
        "arch"    : "YOLOv8s",
    },
    "yolov8s_2class": {
        "label"   : "YOLOv8s — 2 Class",
        "desc"    : "Early Blight + Late Blight (augmented dataset)",
        "path"    : BASE / "models" / "yolov8s" / "best_2class.pt",
        "classes" : ["Early_Blight", "Late_Blight"],
        "map"     : "0.626",
        "arch"    : "YOLOv8s",
    },
    "yolov8m_clean": {
        "label"   : "YOLOv8m — Clean ⭐ BEST",
        "desc"    : "Early Blight + Late Blight (clean unique images)",
        "path"    : BASE / "models" / "yolov8m" / "best_clean.pt",
        "classes" : ["Early_Blight", "Late_Blight"],
        "map"     : "0.691",
        "arch"    : "YOLOv8m",
    },
    "yolov8m_merged": {
        "label"   : "YOLOv8m — Merged",
        "desc"    : "Early Blight + Late Blight (studio + field images)",
        "path"    : BASE / "models" / "yolov8m" / "best_merged.pt",
        "classes" : ["Early_Blight", "Late_Blight"],
        "map"     : "0.667",
        "arch"    : "YOLOv8m",
    },
}

CLASS_COLORS_BGR = {
    "Early_Blight"      : (50,  100, 255),
    "Late_Blight"       : (255, 180,  50),
    "Septoria_Leaf_Spot": (50,  220,  50),
}

CONF_THRESHOLD = 0.25
IOU_THRESHOLD  = 0.45

# ── App setup ─────────────────────────────────────────────────────────────────
FRONTEND = BASE / "pipeline" / "stage4_inference" / "frontend"
app      = Flask(__name__, static_folder=str(FRONTEND))

device = "0" if torch.cuda.is_available() else "cpu"

# Cache loaded models
loaded_models = {}

def get_model(model_key):
    if model_key not in loaded_models:
        cfg  = MODELS[model_key]
        print(f"Loading {cfg['label']}...")
        loaded_models[model_key] = YOLO(str(cfg["path"]))
        print(f"  Loaded ✅")
    return loaded_models[model_key]

# Preload best model on startup
print("=" * 55)
print("TomatoScan — Multi-Model Detection Server")
print("=" * 55)
print(f"  Device : {'CUDA (RTX 4060)' if device == '0' else 'CPU'}")
get_model("yolov8m_clean")
print(f"  Ready  : http://localhost:5000")
print("=" * 55)


# ── Helpers ───────────────────────────────────────────────────────────────────
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


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(str(FRONTEND), "index.html")


@app.route("/models", methods=["GET"])
def list_models():
    return jsonify({
        key: {
            "label"  : v["label"],
            "desc"   : v["desc"],
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

    cfg        = MODELS[model_key]
    class_names = cfg["classes"]

    file_bytes = np.frombuffer(request.files["image"].read(), np.uint8)
    img        = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Could not decode image"}), 400

    # Blank image check
    if float(np.std(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))) < 10:
        return jsonify({
            "error"         : "Image appears blank or invalid",
            "valid"         : False,
            "detections"    : [],
            "diseases_found": [],
            "co_occurrence" : False,
            "total_boxes"   : 0,
            "annotated_image": encode_image(img),
        })

    model   = get_model(model_key)
    results = model.predict(
        img,
        conf    = CONF_THRESHOLD,
        iou     = IOU_THRESHOLD,
        device  = device,
        verbose = False,
    )

    h, w = img.shape[:2]
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
            "annotated_image": encode_image(img),
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
            "annotated_image": encode_image(draw_detections(img, detections)),
        })

    diseases_found = sorted(set(d["class_name"] for d in detections))
    co_occurrence  = len(diseases_found) >= 2

    return jsonify({
        "valid"          : True,
        "detections"     : detections,
        "diseases_found" : diseases_found,
        "co_occurrence"  : co_occurrence,
        "total_boxes"    : len(detections),
        "annotated_image": encode_image(draw_detections(img, detections)),
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
