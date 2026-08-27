"""
Quick leaf-gate retrain on PlantVillage:
  PASS  = tomato leaf folders
  REJECT = REJECT folder

Saves improved weights to ml/models/gate_leaf.pth
Does not modify Fruit gate.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

BASE_DIR = Path(__file__).resolve().parents[2]
PV_ROOT = BASE_DIR / "datasets" / "PlantVillage"
OUT_PATH = BASE_DIR / "ml" / "models" / "gate_leaf.pth"
SEED = 42
BATCH = 16
EPOCHS = 8
LR = 1e-4
VAL_RATIO = 0.2


class LeafGateDataset(Dataset):
    def __init__(self, samples, transform):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        return self.transform(img), torch.tensor([label], dtype=torch.float32)


def collect_samples():
    samples = []
    for folder in sorted(PV_ROOT.iterdir()):
        if not folder.is_dir():
            continue
        label = 0.0 if folder.name == "REJECT" else 1.0
        for p in folder.iterdir():
            if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                samples.append((str(p), label))
    return samples


def stratified_split(samples, val_ratio=0.2):
    by_label = {0.0: [], 1.0: []}
    for s in samples:
        by_label[s[1]].append(s)
    train, val = [], []
    for label, items in by_label.items():
        random.shuffle(items)
        n_val = max(1, int(len(items) * val_ratio))
        val.extend(items[:n_val])
        train.extend(items[n_val:])
    random.shuffle(train)
    random.shuffle(val)
    return train, val


def build_model():
    try:
        weights = models.MobileNet_V2_Weights.IMAGENET1K_V1
        model = models.mobilenet_v2(weights=weights)
    except Exception:
        model = models.mobilenet_v2(weights=None)
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.last_channel, 256),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(256, 1),
    )
    return model


def run_epoch(model, loader, criterion, optimizer=None, device="cpu"):
    train = optimizer is not None
    model.train(train)
    total_loss, correct, total = 0.0, 0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        with torch.set_grad_enabled(train):
            logits = model(x)
            loss = criterion(logits, y)
            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        probs = torch.sigmoid(logits)
        preds = (probs > 0.5).float()
        correct += (preds == y).sum().item()
        total += y.numel()
        total_loss += loss.item() * y.size(0)
    return total_loss / max(total, 1), correct / max(total, 1)


def main():
    random.seed(SEED)
    torch.manual_seed(SEED)
    if not PV_ROOT.exists():
        raise SystemExit(f"PlantVillage not found: {PV_ROOT}")

    samples = collect_samples()
    train_s, val_s = stratified_split(samples, VAL_RATIO)
    print(f"train={len(train_s)} val={len(val_s)}")

    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(0.15, 0.15, 0.1),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    train_loader = DataLoader(LeafGateDataset(train_s, train_tf), batch_size=BATCH, shuffle=True)
    val_loader = DataLoader(LeafGateDataset(val_s, eval_tf), batch_size=BATCH)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model().to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    best_acc = -1.0
    best_state = None
    for epoch in range(1, EPOCHS + 1):
        tr_loss, tr_acc = run_epoch(model, train_loader, criterion, optimizer, device)
        va_loss, va_acc = run_epoch(model, val_loader, criterion, None, device)
        print(
            f"epoch {epoch}/{EPOCHS} "
            f"train_loss={tr_loss:.4f} train_acc={tr_acc:.3f} "
            f"val_loss={va_loss:.4f} val_acc={va_acc:.3f}"
        )
        if va_acc > best_acc:
            best_acc = va_acc
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is None:
        raise SystemExit("Training failed to produce weights")

    model.load_state_dict(best_state)
    torch.save(model.state_dict(), OUT_PATH)
    print(f"Saved improved gate to {OUT_PATH}")
    print(f"Best val accuracy: {best_acc:.3f}")


if __name__ == "__main__":
    main()
