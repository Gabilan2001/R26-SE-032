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
MODEL_PATH = os.path.join(BASE_DIR, "model", "tomato_model.pth")
CLASS_PATH = os.path.join(BASE_DIR, "model", "class_names.json")

with open(CLASS_PATH, "r") as f:
    class_names = json.load(f)

# ─────────────────────────────
# Solutions for each class
# ─────────────────────────────
solutions = {
    "Healthy": {
        "description": "Your tomato plant is healthy!",
        "symptoms": "No deficiency symptoms detected",
        "solution": "No action needed. Continue regular care.",
        "fertilizer": "Maintain current fertilization schedule"
    },
    "Nitrogen": {
        "description": "Nitrogen deficiency detected",
        "symptoms": "Yellowing of older/lower leaves, stunted growth, pale green color",
        "solution": "Apply nitrogen-rich fertilizer immediately",
        "fertilizer": "Apply Urea (46-0-0) at 200kg/hectare or use liquid nitrogen fertilizer"
    },
    "Potassium": {
        "description": "Potassium deficiency detected",
        "symptoms": "Brown scorched leaf edges, weak stems, poor fruit quality",
        "solution": "Apply potassium fertilizer",
        "fertilizer": "Apply Potassium Sulfate (0-0-50) at 150kg/hectare"
    },
    "Nitrogen_Potassium": {
        "description": "Nitrogen and Potassium deficiency detected",
        "symptoms": "Yellowing leaves with brown edges, stunted growth",
        "solution": "Apply combined N-K fertilizer",
        "fertilizer": "Apply NPK fertilizer (15-0-15) at 250kg/hectare"
    },
    "Phosphorus": {
        "description": "Phosphorus deficiency detected",
        "symptoms": "Purple or reddish color on leaf underside, dark green leaves, poor root growth",
        "solution": "Apply phosphorus fertilizer",
        "fertilizer": "Apply Superphosphate at 250kg/hectare or bone meal"
    },
    "Iron_Deficiency": {
        "description": "Iron deficiency detected",
        "symptoms": "Yellowing of new/young leaves with green veins (interveinal chlorosis)",
        "solution": "Apply iron fertilizer as foliar spray",
        "fertilizer": "Spray Iron Chelate (FeSO4) solution on leaves every 2 weeks"
    }
}

# ─────────────────────────────
# Load model
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
# Image transform
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
        "message": "Tomato Leaf Nutrient Deficiency API",
        "status": "running",
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
        img = Image.open(file.stream).convert('RGB')
        img_tensor = transform(img).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = model(img_tensor)
            probs   = torch.nn.functional.softmax(outputs, dim=1)
            conf, pred = torch.max(probs, 1)

        class_name   = class_names[pred.item()]
        confidence   = round(conf.item() * 100, 2)
        solution     = solutions.get(class_name, {})

        return jsonify({
            "class":       class_name,
            "confidence":  confidence,
            "description": solution.get("description", ""),
            "symptoms":    solution.get("symptoms", ""),
            "solution":    solution.get("solution", ""),
            "fertilizer":  solution.get("fertilizer", "")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)