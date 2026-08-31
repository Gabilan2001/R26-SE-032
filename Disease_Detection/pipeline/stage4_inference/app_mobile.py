"""
app_mobile.py
=============
Lean, single-model Flask backend for the TomatoDoc mobile app's Disease
module. This is the PRODUCT backend -- separate from app.py, which stays a
multi-model research/comparison tool (5 models, used for the paper) and is
not meant to be deployed.

Only the one validated final model is served here: YOLOv8m 4-class,
native-640 (Early_Blight, Late_Blight, Healthy, Leaf_Miner). Same leaf
validation, background removal, and Gemini RAG treatment system as app.py --
that logic is unchanged, just trimmed to one model so this is lighter to run
and cheap to host (Cloud Run, etc.).

Port 5002 (not 5000) -- avoids colliding with the Nutrient module's backend
and app.py's research/testing server, in case more than one needs to run at
once during a full-app demo.

Run from this folder:
  python app_mobile.py
"""

import base64
import os
from pathlib import Path

import cv2
import numpy as np
import torch
from flask import Flask, request, jsonify
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

# ── Scan History (Firestore) ────────────────────────────────────────────────────
# Independent of the Nutrient/Fruit modules' shared MongoDB + auth backend --
# this module owns its own history/stats, no login required. On Cloud Run the
# attached service account authenticates automatically (Application Default
# Credentials); for local runs, `gcloud auth application-default login` once.
try:
    from google.cloud import firestore
    # Explicit project (rather than relying on ambient auto-detection) --
    # works reliably both on Cloud Run and for local `python app_mobile.py`
    # runs authenticated via `gcloud auth application-default login`.
    FIRESTORE_PROJECT = os.getenv("FIRESTORE_PROJECT", "tomatodoc-hosting")
    fs_client = firestore.Client(project=FIRESTORE_PROJECT)
    FIRESTORE_AVAILABLE = True
except Exception as e:
    fs_client = None
    FIRESTORE_AVAILABLE = False
    print(f"  Firestore unavailable (history/stats disabled): {e}")

SCANS_COLLECTION = "disease_scans"

# ── Leaf Validator ────────────────────────────────────────────────────────────
from torchvision import models, transforms
import torch.nn as nn

BASE = Path(__file__).resolve().parents[2]  # .../Disease_Detection
VALIDATOR_PATH = BASE / "models" / "leaf_validator.pth"
VALIDATOR_THRESHOLD = 0.5  # was 0.75 -- too strict once training data got realistically
# harder (no longer near-1.0 confidence on everything); a correct-but-moderate
# "tomato_leaf" call like 0.66 was getting rejected outright. Argmax still has
# to BE tomato_leaf either way, so this only affects genuine tomato calls
# sitting in the 0.5-0.75 range, not other-class predictions.

device = "0" if torch.cuda.is_available() else "cpu"
torch_device = "cuda" if torch.cuda.is_available() else "cpu"

# 3-class as of the retrain: tomato_leaf / other_plant_leaf / random_object
# (was a 2-class tomato-vs-not validator before -- that couldn't tell a wrong
# plant species from a non-leaf object, so both got the same generic error).
VALIDATOR_CLASS_NAMES = ["tomato_leaf", "other_plant_leaf", "random_object"]
LEAF_VALIDATOR_MESSAGES = {
    "other_plant_leaf": "This looks like a different plant's leaf, not a tomato leaf. Please upload a photo of a tomato leaf.",
    "random_object": "This doesn't look like a leaf at all. Please upload a clear photo of a tomato leaf.",
}

def load_leaf_validator():
    ckpt = torch.load(str(VALIDATOR_PATH), map_location="cpu", weights_only=False)
    m = models.efficientnet_b0(weights=None)
    m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(VALIDATOR_CLASS_NAMES))
    m.load_state_dict(ckpt["model_state_dict"])
    m.eval().to(torch_device)
    return m

def classify_leaf(img_bgr, validator_model):
    """Returns (is_valid_tomato_leaf, predicted_class_name, tomato_leaf_confidence)."""
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    t = transform(pil).unsqueeze(0).to(torch_device)
    with torch.no_grad():
        probs = torch.softmax(validator_model(t), dim=1)[0].cpu().numpy()
    tomato_conf = float(probs[0])
    pred_class = VALIDATOR_CLASS_NAMES[int(np.argmax(probs))]
    is_valid = pred_class == "tomato_leaf" and tomato_conf >= VALIDATOR_THRESHOLD
    return is_valid, pred_class, round(tomato_conf, 4)

# ── The one final model ────────────────────────────────────────────────────────
MODEL_PATH = BASE / "models" / "yolov8m_final" / "weights" / "best.pt"
CLASS_NAMES = ["Early_Blight", "Late_Blight", "Healthy", "Leaf_Miner"]

CLASS_COLORS_BGR = {
    "Early_Blight": (50, 100, 255),
    "Late_Blight": (255, 180, 50),
    "Healthy": (60, 200, 60),
    "Leaf_Miner": (0, 165, 255),
}

CONF_THRESHOLD = 0.30
IOU_THRESHOLD = 0.45

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

print("=" * 55)
print("TomatoDoc — Disease Detection Backend (Mobile)")
print("=" * 55)
print(f"  Device : {'CUDA' if torch.cuda.is_available() else 'CPU'}")
print("  Loading YOLOv8m (native-640, final)...")
model = YOLO(str(MODEL_PATH))
print("  Loaded ✅")
print("  Loading leaf validator...")
leaf_validator = load_leaf_validator()
print("  Leaf validator loaded ✅")
print(f"  Ready  : http://0.0.0.0:5002")
print("=" * 55)


# ── Helpers ───────────────────────────────────────────────────────────────────
def remove_background(img_bgr):
    """Remove background from BGR image. Falls back to original if it fails."""
    try:
        pil_img = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        pil_no_bg = rembg_remove(pil_img)
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
        name = det["class_name"]
        conf = det["confidence"]
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


def save_scan_history(detections, diseases_found, co_occurrence, treatment):
    """Best-effort save of a completed scan to Firestore. Never blocks or
    fails the /predict response -- history is a bonus feature, not core."""
    if not FIRESTORE_AVAILABLE:
        return
    try:
        # Slim detection records for storage/listing -- box coords aren't
        # needed for history/stats, just what disease + how confident.
        slim_detections = [
            {"class_name": d["class_name"], "confidence": d["confidence"]}
            for d in detections
        ]
        fs_client.collection(SCANS_COLLECTION).add({
            "created_at": firestore.SERVER_TIMESTAMP,
            "detections": slim_detections,
            "diseases_found": diseases_found,
            "co_occurrence": co_occurrence,
            "treatment_answer": treatment["answer"] if treatment else None,
            "treatment_sources": treatment["sources"] if treatment else [],
        })
    except Exception as e:
        print(f"  Firestore save failed: {e}")


def get_treatment(diseases_found):
    if not RAG_AVAILABLE or not diseases_found:
        return None
    try:
        treatable = [d for d in diseases_found if d != "Healthy"]
        if not treatable:
            return None
        readable = [d.replace("_", " ") for d in treatable]
        if len(readable) == 1:
            query = (f"What treatment and dosage for {readable[0]} on tomato, "
                      f"including how much to use for one plant")
        else:
            disease_phrase = ", ".join(readable[:-1]) + " and " + readable[-1]
            query = (f"These were detected together on the same tomato plant: {disease_phrase}. "
                      f"Give a separate complete treatment (including dosage and how much for one plant) "
                      f"for EACH one, then explain whether any of these can be treated together with "
                      f"fewer sprays or need to stay separate.")
        result = query_rag(query, diseases=treatable)
        return {"answer": result["answer"], "sources": result["sources"]}
    except Exception as e:
        print(f"  RAG query failed: {e}")
        return None


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict():
    # Testing toggle from the mobile app's (hidden, dev-only) Scan Settings
    # screen -- lets us A/B compare detection with vs. without the
    # background-removal step. Defaults to on (normal behavior) whenever
    # it's absent, matching the toggle's own default-off/reset-on-launch
    # design on the client side.
    skip_bg_removal = request.form.get("skip_bg_removal", "false").lower() == "true"

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file_bytes = np.frombuffer(request.files["image"].read(), np.uint8)
    original_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if original_img is None:
        return jsonify({"error": "Could not decode image"}), 400

    if float(np.std(cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY))) < 10:
        return jsonify({
            "error": "Image appears blank or invalid",
            "valid": False, "detections": [], "diseases_found": [],
            "co_occurrence": False, "total_boxes": 0,
            "annotated_image": encode_image(original_img),
        })

    valid_leaf, leaf_class, leaf_conf = classify_leaf(original_img, leaf_validator)
    if not valid_leaf:
        print(f"  Leaf REJECTED ❌ predicted={leaf_class} tomato_conf={leaf_conf:.2f} (threshold={VALIDATOR_THRESHOLD})")
        msg = LEAF_VALIDATOR_MESSAGES.get(leaf_class, "Not a tomato leaf image.")
        return jsonify({
            "error": f"{msg} (confidence: {leaf_conf:.0%})",
            "valid": False, "leaf_class": leaf_class, "leaf_conf": leaf_conf,
            "detections": [], "diseases_found": [],
            "co_occurrence": False, "total_boxes": 0,
            "annotated_image": encode_image(original_img),
        })

    print(f"  Leaf validated ✅ (confidence: {leaf_conf:.2f})")
    if skip_bg_removal:
        print("  Skipping background removal (testing toggle) ⏭")
        clean_img = original_img
    else:
        print("  Removing background...")
        clean_img = remove_background(original_img)
        print("  Background removed ✅")

    results = model.predict(clean_img, conf=CONF_THRESHOLD, iou=IOU_THRESHOLD,
                             device=device, verbose=False)

    h, w = original_img.shape[:2]
    detections = []
    for r in results:
        if r.boxes is None:
            continue
        for box in r.boxes:
            cls_idx = int(box.cls.item())
            conf = float(box.conf.item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            name = CLASS_NAMES[cls_idx] if cls_idx < len(CLASS_NAMES) else f"class_{cls_idx}"
            detections.append({
                "class_name": name, "class_idx": cls_idx, "confidence": round(conf, 4),
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "box_area": round((x2 - x1) * (y2 - y1) / (w * h), 4),
            })

    if len(detections) == 0:
        return jsonify({
            "error": "No disease detected — ensure image shows a tomato leaf with visible symptoms",
            "valid": False, "detections": [], "diseases_found": [],
            "co_occurrence": False, "total_boxes": 0,
            "annotated_image": encode_image(original_img),
        })

    diseases_found = sorted(set(d["class_name"] for d in detections))
    co_occurrence = len([d for d in diseases_found if d != "Healthy"]) >= 2
    annotated = draw_detections(original_img, detections)

    # Treatment is fetched separately via /treatment, called by the client
    # right after this response -- keeps /predict fast (a few seconds) so
    # the result screen can show the detection immediately instead of
    # making the user wait up to ~90s for the RAG/Gemini call before
    # seeing anything at all.
    return jsonify({
        "valid": True,
        "detections": detections,
        "diseases_found": diseases_found,
        "co_occurrence": co_occurrence,
        "total_boxes": len(detections),
        "annotated_image": encode_image(annotated),
        "treatment": None,
        "bg_removal_applied": not skip_bg_removal,
        "model_info": {
            "label": "YOLOv8m (4-class, native-640)",
            "classes": CLASS_NAMES,
            "conf_thr": CONF_THRESHOLD,
            "iou_thr": IOU_THRESHOLD,
            "device": "CUDA" if torch.cuda.is_available() else "CPU",
        },
    })


@app.route("/treatment", methods=["POST"])
def treatment():
    """Second phase of a scan -- called by the client right after /predict
    returns, once the detection result is already showing. Also owns the
    Firestore history save (needs the full picture: detections + whatever
    treatment came back, so this is the one place that saves it -- covers
    Healthy-only scans too, since the client always calls this regardless
    of whether there's anything treatable, just without showing a loading
    spinner for that case)."""
    data = request.get_json(force=True) or {}
    detections = data.get("detections", [])
    diseases_found = data.get("diseases_found", [])
    co_occurrence = bool(data.get("co_occurrence", False))

    result = get_treatment(diseases_found)
    save_scan_history(detections, diseases_found, co_occurrence, result)

    return jsonify({"treatment": result})


@app.route("/history", methods=["GET"])
def get_history():
    if not FIRESTORE_AVAILABLE:
        return jsonify({"error": "History unavailable", "history": []}), 503

    limit = min(int(request.args.get("limit", 30)), 100)
    docs = (
        fs_client.collection(SCANS_COLLECTION)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    history = []
    for d in docs:
        item = d.to_dict()
        item["id"] = d.id
        ts = item.get("created_at")
        item["created_at"] = ts.isoformat() if ts else None
        history.append(item)

    return jsonify({"history": history})


@app.route("/stats", methods=["GET"])
def get_stats():
    if not FIRESTORE_AVAILABLE:
        return jsonify({"error": "Stats unavailable"}), 503

    docs = list(fs_client.collection(SCANS_COLLECTION).stream())

    class_counts = {}
    co_occurrence_count = 0
    for d in docs:
        item = d.to_dict()
        for disease in item.get("diseases_found", []):
            class_counts[disease] = class_counts.get(disease, 0) + 1
        if item.get("co_occurrence"):
            co_occurrence_count += 1

    return jsonify({
        "total_scans": len(docs),
        "class_counts": class_counts,
        "co_occurrence_count": co_occurrence_count,
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "device": "CUDA" if torch.cuda.is_available() else "CPU",
        "model": "yolov8m_final (native-640, 4-class)",
        "firestore": FIRESTORE_AVAILABLE,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
