"""
train_leaf_validator.py
=======================
Trains a binary EfficientNet-B0 classifier:
  Class 0 → tomato_leaf  (all tomato leaf types)
  Class 1 → not_tomato   (Intel Image Classification scenes)

Output:
  leaf_validator.pth  → saved to models folder

Run from stage4_inference folder:
  python train_leaf_validator.py
"""

import random
import shutil
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
OUT_MODEL  = BASE / "models" / "leaf_validator.pth"

# Tomato leaf sources (positive class)
TOMATO_DIRS = [
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_healthy"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Early_blight"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Late_blight") if Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Late_blight").exists() else
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\test\Tomato_Late_blight"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Bacterial_spot"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Septoria_leaf_spot"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_YellowLeaf_Curl_Virus"),
    # Also include your YOLO training images
    BASE / "data" / "splits" / "train" / "images",
]

# Not-tomato sources (negative class)
NOT_TOMATO_DIRS = [
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\buildings"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\forest"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\glacier"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\mountain"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\sea"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\street"),
]

# ── Config ────────────────────────────────────────────────────────────────────
TOMATO_LIMIT    = 2000    # max tomato leaf images to use
NOT_TOMATO_LIMIT = 2000   # max not-tomato images to use
VAL_SPLIT       = 0.2
IMG_SIZE        = 224
BATCH_SIZE      = 32
EPOCHS          = 15
LR              = 1e-4
THRESHOLD       = 0.75    # confidence to confirm tomato leaf

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Transforms ────────────────────────────────────────────────────────────────
TRAIN_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

VAL_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# ── Dataset ───────────────────────────────────────────────────────────────────
class LeafDataset(Dataset):
    def __init__(self, samples, transform):
        self.samples   = samples  # list of (path, label)
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            img = Image.open(path).convert("RGB")
            img = self.transform(img)
        except:
            img = torch.zeros(3, IMG_SIZE, IMG_SIZE)
        return img, label


# ── Collect images ────────────────────────────────────────────────────────────
def collect_images(dirs, limit):
    exts = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
    all_imgs = []
    for d in dirs:
        if not d.exists():
            print(f"  Warning: {d} not found — skipping")
            continue
        imgs = [p for p in d.iterdir() if p.suffix in exts]
        all_imgs.extend(imgs)
        print(f"  {d.name:<40} {len(imgs)} images")

    random.shuffle(all_imgs)
    return all_imgs[:limit]


# ── Build model ───────────────────────────────────────────────────────────────
def build_model():
    m = models.efficientnet_b0(weights="IMAGENET1K_V1")
    m.classifier[1] = nn.Linear(m.classifier[1].in_features, 2)
    return m.to(device)


# ── Train ─────────────────────────────────────────────────────────────────────
def train():
    random.seed(42)
    torch.manual_seed(42)

    print("=" * 55)
    print("Leaf Validator — Binary Classifier Training")
    print("=" * 55)
    print(f"  Device : {device}")

    # Collect images
    print("\n  Collecting tomato leaf images...")
    tomato_imgs = collect_images(TOMATO_DIRS, TOMATO_LIMIT)
    print(f"  Total tomato leaf : {len(tomato_imgs)}")

    print("\n  Collecting not-tomato images...")
    not_tomato_imgs = collect_images(NOT_TOMATO_DIRS, NOT_TOMATO_LIMIT)
    print(f"  Total not-tomato  : {len(not_tomato_imgs)}")

    # Build samples
    samples = (
        [(p, 0) for p in tomato_imgs] +
        [(p, 1) for p in not_tomato_imgs]
    )
    random.shuffle(samples)

    print(f"\n  Total samples : {len(samples)}")
    print(f"  Tomato leaf   : {len(tomato_imgs)} (class 0)")
    print(f"  Not tomato    : {len(not_tomato_imgs)} (class 1)")

    # Train/val split
    split = int(len(samples) * (1 - VAL_SPLIT))
    train_samples = samples[:split]
    val_samples   = samples[split:]

    print(f"  Train : {len(train_samples)}")
    print(f"  Val   : {len(val_samples)}")

    train_ds = LeafDataset(train_samples, TRAIN_TRANSFORM)
    val_ds   = LeafDataset(val_samples,   VAL_TRANSFORM)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0, pin_memory=True)

    # Model
    model     = build_model()
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    best_val_acc = 0.0

    print("\n  Training...\n")
    print(f"  {'Epoch':<8} {'Train Loss':<14} {'Train Acc':<14} {'Val Loss':<14} {'Val Acc':<10}")
    print("  " + "-" * 60)

    for epoch in range(1, EPOCHS + 1):
        # ── Train ──────────────────────────────────────────────────
        model.train()
        train_loss = train_correct = train_total = 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            out  = model(imgs)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()
            train_loss    += loss.item() * imgs.size(0)
            preds          = out.argmax(dim=1)
            train_correct += (preds == labels).sum().item()
            train_total   += imgs.size(0)

        train_loss /= train_total
        train_acc   = train_correct / train_total

        # ── Val ────────────────────────────────────────────────────
        model.eval()
        val_loss = val_correct = val_total = 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                out  = model(imgs)
                loss = criterion(out, labels)
                val_loss    += loss.item() * imgs.size(0)
                preds        = out.argmax(dim=1)
                val_correct += (preds == labels).sum().item()
                val_total   += imgs.size(0)

        val_loss /= val_total
        val_acc   = val_correct / val_total

        scheduler.step()

        marker = " ← best" if val_acc > best_val_acc else ""
        print(f"  {epoch:<8} {train_loss:<14.4f} {train_acc:<14.4f} {val_loss:<14.4f} {val_acc:.4f}{marker}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                "model_state_dict": model.state_dict(),
                "classes"         : ["tomato_leaf", "not_tomato"],
                "threshold"       : THRESHOLD,
                "best_val_acc"    : best_val_acc,
                "img_size"        : IMG_SIZE,
            }, str(OUT_MODEL))

    print(f"\n  Best val accuracy : {best_val_acc:.4f}")
    print(f"  Model saved       → {OUT_MODEL}")

    # ── Final evaluation ───────────────────────────────────────────
    print("\n  Running final evaluation on val set...")
    model.eval()
    all_preds  = []
    all_labels = []
    with torch.no_grad():
        for imgs, labels in val_loader:
            imgs = imgs.to(device)
            out  = model(imgs)
            preds = out.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy())

    print("\n  Classification Report:")
    print(classification_report(all_labels, all_preds,
                                 target_names=["tomato_leaf", "not_tomato"]))

    cm = confusion_matrix(all_labels, all_preds)
    print("  Confusion Matrix:")
    print(f"                Pred tomato  Pred not_tomato")
    print(f"  GT tomato      {cm[0][0]:>10}  {cm[0][1]:>15}")
    print(f"  GT not_tomato  {cm[1][0]:>10}  {cm[1][1]:>15}")

    print("\n  Training complete ✅")
    print("=" * 55)


if __name__ == "__main__":
    train()
