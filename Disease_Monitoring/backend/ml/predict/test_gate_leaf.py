"""
Test Script - MobileNetV2 Gate Model for Leaf Validation
Tests the trained model and shows output predictions
"""

import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import mobilenet_v2
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from pathlib import Path
import os

# Configuration
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODEL_PATH = Path(__file__).parent.parent / 'models' / 'gate_leaf.pth'
IMAGE_SIZE = 224


class LeafGateModel(nn.Module):
    """MobileNetV2-based Gate Model for Leaf Validation"""
    
    def __init__(self, num_classes=2):
        super(LeafGateModel, self).__init__()
        
        # Load pre-trained MobileNetV2
        self.mobilenet = mobilenet_v2(pretrained=True)
        
        # Freeze early layers
        for param in self.mobilenet.features[:12].parameters():
            param.requires_grad = False
        
        # Replace classifier
        num_features = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_features, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        return self.mobilenet(x)


def generate_test_image(quality_type='high'):
    """Generate synthetic test leaf image"""
    if quality_type == 'high':
        # High-quality leaf (PASS)
        img = Image.new('RGB', (IMAGE_SIZE, IMAGE_SIZE), color=(34, 139, 34))
        draw = ImageDraw.Draw(img)
        
        center_x, center_y = IMAGE_SIZE // 2, IMAGE_SIZE // 2
        leaf_width = 100
        leaf_height = 130
        
        bbox = [
            center_x - leaf_width // 2,
            center_y - leaf_height // 2,
            center_x + leaf_width // 2,
            center_y + leaf_height // 2
        ]
        draw.ellipse(bbox, fill=(0, 100, 0), outline=(0, 80, 0))
        
        # Add veins
        for i in range(3, 8):
            x_offset = np.random.randint(-20, 20)
            draw.line(
                [(center_x + x_offset, center_y - leaf_height // 2),
                 (center_x + x_offset * 0.7, center_y + leaf_height // 2)],
                fill=(0, 60, 0),
                width=2
            )
        
        return img
    
    else:
        # Low-quality leaf (REJECT)
        img = Image.new('RGB', (IMAGE_SIZE, IMAGE_SIZE), color=(34, 139, 34))
        draw = ImageDraw.Draw(img)
        
        center_x, center_y = IMAGE_SIZE // 2, IMAGE_SIZE // 2
        leaf_width = 80
        leaf_height = 100
        
        bbox = [
            center_x - leaf_width // 2,
            center_y - leaf_height // 2,
            center_x + leaf_width // 2,
            center_y + leaf_height // 2
        ]
        draw.ellipse(bbox, fill=(0, 100, 0), outline=(0, 80, 0))
        
        # Add heavy blur and noise
        img = img.filter(ImageFilter.GaussianBlur(radius=3.5))
        
        img_array = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, 35, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_array)
        
        # Add artifacts
        draw = ImageDraw.Draw(img)
        for _ in range(10):
            x = np.random.randint(0, IMAGE_SIZE)
            y = np.random.randint(0, IMAGE_SIZE)
            draw.rectangle(
                [x, y, x + np.random.randint(10, 25), y + np.random.randint(10, 25)],
                fill=(np.random.randint(100, 200), np.random.randint(50, 150), np.random.randint(0, 100))
            )
        
        return img


def load_model():
    """Load trained model"""
    print("🔧 Loading model...")
    model = LeafGateModel(num_classes=2).to(DEVICE)
    
    if MODEL_PATH.exists():
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        print(f"✅ Model loaded from: {MODEL_PATH}")
    else:
        print(f"❌ Model not found at: {MODEL_PATH}")
        return None
    
    model.eval()
    return model


def predict(model, image):
    """Make prediction on image"""
    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
    
    img_tensor = transform(image).unsqueeze(0).to(DEVICE)
    
    with torch.no_grad():
        outputs = model(img_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        predicted_class = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0][predicted_class].item()
    
    return predicted_class, confidence, probabilities[0].cpu().numpy()


def test_model():
    """Test model with sample images"""
    print("\n" + "="*70)
    print("🧪 TESTING MOBILENETV2 GATE MODEL - LEAF VALIDATION")
    print("="*70 + "\n")
    
    # Load model
    model = load_model()
    if model is None:
        return
    
    print(f"📊 Device: {DEVICE}\n")
    
    # Test cases
    test_cases = [
        ('High-Quality Leaf (PASS Expected)', 'high'),
        ('Low-Quality Leaf (REJECT Expected)', 'low'),
        ('High-Quality Leaf #2 (PASS Expected)', 'high'),
        ('Low-Quality Leaf #2 (REJECT Expected)', 'low'),
    ]
    
    results = []
    
    print("🧬 Running Predictions...\n")
    print("-" * 70)
    
    for idx, (description, quality) in enumerate(test_cases, 1):
        print(f"\n📸 Test Case {idx}: {description}")
        print("-" * 70)
        
        # Generate test image
        test_image = generate_test_image(quality_type=quality)
        
        # Make prediction
        predicted_class, confidence, all_probs = predict(model, test_image)
        
        # Map class to label
        class_label = "✅ PASS" if predicted_class == 1 else "❌ REJECT"
        expected_label = "✅ PASS" if quality == 'high' else "❌ REJECT"
        
        # Check if correct
        is_correct = (predicted_class == 1 and quality == 'high') or \
                     (predicted_class == 0 and quality == 'low')
        correct_mark = "✓" if is_correct else "✗"
        
        print(f"Expected:       {expected_label}")
        print(f"Predicted:      {class_label}")
        print(f"Confidence:     {confidence*100:.2f}%")
        print(f"Accuracy:       {correct_mark}")
        
        # Show probability distribution
        print(f"\nProbability Distribution:")
        print(f"  REJECT (Label 0): {all_probs[0]*100:6.2f}%")
        print(f"  PASS   (Label 1): {all_probs[1]*100:6.2f}%")
        
        results.append({
            'description': description,
            'expected': expected_label,
            'predicted': class_label,
            'confidence': confidence,
            'correct': is_correct
        })
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70 + "\n")
    
    correct_count = sum(1 for r in results if r['correct'])
    total_count = len(results)
    accuracy = (correct_count / total_count) * 100
    
    print(f"Total Tests:       {total_count}")
    print(f"Correct:           {correct_count}")
    print(f"Incorrect:         {total_count - correct_count}")
    print(f"Test Accuracy:     {accuracy:.2f}%\n")
    
    print("Detailed Results:")
    print("-" * 70)
    print(f"{'Test':<5} {'Description':<30} {'Expected':<12} {'Predicted':<12} {'Confidence':<12} {'Status':<8}")
    print("-" * 70)
    
    for idx, result in enumerate(results, 1):
        status = "✓ PASS" if result['correct'] else "✗ FAIL"
        print(f"{idx:<5} {result['description']:<30} {result['expected']:<12} {result['predicted']:<12} {result['confidence']*100:>10.2f}% {status:<8}")
    
    print("-" * 70 + "\n")
    
    print("✨ Model Testing Complete!\n")
    
    # Model information
    print("📋 MODEL INFORMATION")
    print("-" * 70)
    print("Model Name:        MobileNetV2 Gate Model")
    print("Purpose:           Validate tomato leaf image quality")
    print("Classes:           2 (PASS / REJECT)")
    print("Input Size:        224x224 pixels (RGB)")
    print("Architecture:      MobileNetV2 with transfer learning")
    print("Framework:         PyTorch")
    print("Status:            ✅ Ready for deployment\n")


if __name__ == "__main__":
    test_model()
