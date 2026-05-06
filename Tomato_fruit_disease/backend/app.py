from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import json
import os

app = Flask(__name__)
CORS(app)

# ─────────────────────────────
# Load class names
# ─────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "disease_model.pth")
CLASS_PATH = os.path.join(BASE_DIR, "model", "disease_class_names.json")

with open(CLASS_PATH, "r") as f:
    class_names = json.load(f)

# ─────────────────────────────
# Solutions
# ─────────────────────────────
solutions = {
    "Anthracnose": {
        "description": "Anthracnose disease detected",
        "symptoms": "Dark sunken spots on fruit, rotting patches, circular lesions",
        "solution": "Remove infected fruits immediately. Apply fungicide.",
        "treatment": "Spray Mancozeb or Copper-based fungicide every 7 days"
    },
    "Bacterial_Spot": {
        "description": "Bacterial Spot disease detected",
        "symptoms": "Small water-soaked spots on fruit, dark raised lesions",
        "solution": "Apply copper-based bactericide. Remove infected plants.",
        "treatment": "Spray Copper Hydroxide at 2g/liter every 5-7 days"
    },
    "Blossom_end_rot": {
        "description": "Blossom End Rot detected",
        "symptoms": "Dark leathery patch at bottom of fruit, sunken dry rot",
        "solution": "Apply calcium fertilizer. Maintain consistent watering.",
        "treatment": "Spray Calcium Nitrate solution at 4g/liter on leaves"
    },
    "Healthy_Tomato": {
        "description": "Your tomato fruit is healthy!",
        "symptoms": "No disease symptoms detected",
        "solution": "No action needed. Continue regular care.",
        "treatment": "Maintain current care schedule"
    },
    "Spotted_wilt_Virus": {
        "description": "Spotted Wilt Virus detected",
        "symptoms": "Bronze/brown spots on fruit, ring patterns, stunted growth",
        "solution": "Remove and destroy infected plants. Control thrips insects.",
        "treatment": "No cure available. Remove infected plants to prevent spread."
    }
}

# ─────────────────────────────
# Load Model
# ─────────────────────────────
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using: {device}")

model = models.mobilenet_v2(weights=None)
model.classifier[1] = nn.Linear(model.last_channel, len(class_names))
model.load_state_dict(
    torch.load(MODEL_PATH, map_location=device, weights_only=False)
)
model = model.to(device)
model.eval()
print(f"Model loaded! Classes: {class_names}")

# ─────────────────────────────
# Transform
# ─────────────────────────────
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    )
])

# ─────────────────────────────
# Routes
# ─────────────────────────────
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Tomato Fruit Disease Detection API",
        "status":  "running",
        "classes": class_names
    })

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        img        = Image.open(file.stream).convert('RGB')
        img_tensor = transform(img).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs    = model(img_tensor)
            probs      = torch.nn.functional.softmax(outputs, dim=1)
            conf, pred = torch.max(probs, 1)

        class_name = class_names[pred.item()]
        confidence = round(conf.item() * 100, 2)
        solution   = solutions.get(class_name, {})
        warning    = ""
        if confidence < 70:
            warning = "Low confidence. Please retake photo with better lighting."

        return jsonify({
            "class":       class_name,
            "confidence":  confidence,
            "warning":     warning,
            "description": solution.get("description", ""),
            "symptoms":    solution.get("symptoms", ""),
            "solution":    solution.get("solution", ""),
            "treatment":   solution.get("treatment", "")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)