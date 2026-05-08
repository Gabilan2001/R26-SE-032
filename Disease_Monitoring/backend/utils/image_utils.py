import cv2
import numpy as np
from PIL import Image
import io

def bytes_to_image(image_bytes: bytes):
    """Convert uploaded file bytes to numpy array"""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((256, 256))
    return np.array(image)

def preprocess_for_model(image_bytes: bytes):
    """Prepare image for PyTorch model"""
    import torch
    img = bytes_to_image(image_bytes)
    img = img / 255.0                          # normalize to 0-1
    img = np.transpose(img, (2, 0, 1))         # HWC to CHW
    img = torch.tensor(img, dtype=torch.float32)
    img = img.unsqueeze(0)                     # add batch dimension
    return img