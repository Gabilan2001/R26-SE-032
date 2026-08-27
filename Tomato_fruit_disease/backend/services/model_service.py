import json
import os

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'disease_model.pth')
CLASS_PATH = os.path.join(BASE_DIR, 'model', 'disease_class_names.json')

with open(CLASS_PATH, 'r', encoding='utf-8') as f:
    class_names = json.load(f)

solutions = {
    "Anthracnose": {
        "description": "Anthracnose disease detected",
        "symptoms": "Dark sunken spots on fruit, rotting patches, circular lesions",
        "solution": "Remove infected fruits immediately. Apply fungicide.",
        "treatment": "Spray Mancozeb or Copper-based fungicide every 7 days",
    },
    "Bacterial_Spot": {
        "description": "Bacterial Spot disease detected",
        "symptoms": "Small water-soaked spots on fruit, dark raised lesions",
        "solution": "Apply copper-based bactericide. Remove infected plants.",
        "treatment": "Spray Copper Hydroxide at 2g/liter every 5-7 days",
    },
    "Blossom_end_rot": {
        "description": "Blossom End Rot detected",
        "symptoms": "Dark leathery patch at bottom of fruit, sunken dry rot",
        "solution": "Apply calcium fertilizer. Maintain consistent watering.",
        "treatment": "Spray Calcium Nitrate solution at 4g/liter on leaves",
    },
    "Healthy_Tomato": {
        "description": "Your tomato fruit is healthy!",
        "symptoms": "No disease symptoms detected",
        "solution": "No action needed. Continue regular care.",
        "treatment": "Maintain current care schedule",
    },
    "Spotted_wilt_Virus": {
        "description": "Spotted Wilt Virus detected",
        "symptoms": "Bronze/brown spots on fruit, ring patterns, stunted growth",
        "solution": "Remove and destroy infected plants. Control thrips insects.",
        "treatment": "No cure available. Remove infected plants to prevent spread.",
    },
}

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = models.mobilenet_v2(weights=None)
model.classifier[1] = nn.Linear(model.last_channel, len(class_names))
model.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=False))
model = model.to(device)
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def predict_image(file_stream):
    img = Image.open(file_stream).convert('RGB')
    img_tensor = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(img_tensor)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        conf, pred = torch.max(probs, 1)

    class_name = class_names[pred.item()]
    confidence = round(conf.item() * 100, 2)
    solution = solutions.get(class_name, {})

    warning = ''
    if confidence < 70:
        warning = 'Low confidence. Please retake photo with better lighting.'

    return {
        'class': class_name,
        'confidence': confidence,
        'warning': warning,
        'description': solution.get('description', ''),
        'symptoms': solution.get('symptoms', ''),
        'solution': solution.get('solution', ''),
        'treatment': solution.get('treatment', ''),
    }

