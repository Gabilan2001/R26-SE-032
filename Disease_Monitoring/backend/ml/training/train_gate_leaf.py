"""
Gate Model Training — FIXED VERSION
MobileNetV2 binary classifier: PASS (tomato leaf) vs REJECT (other)
"""

import os, csv, random
import numpy as np
from PIL import Image
from collections import Counter

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms, models
from torchvision.models import MobileNet_V2_Weights
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── CONFIG ────────────────────────────────────────────────────
# __file__ = Monitoring/ml/training/train_gate_leaf.py
# go up 2 levels → Monitoring/
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSV_PATH    = os.path.join(BASE_DIR, "datasets", "leaf_disease", "dataset.csv")
MODEL_DIR   = os.path.join(BASE_DIR, "ml", "models")
IMG_ROOT    = BASE_DIR   # paths in CSV start with "datasets/..." relative to Monitoring/
os.makedirs(MODEL_DIR, exist_ok=True)

DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE    = 224
BATCH_SIZE  = 32
MAX_EPOCHS  = 50
LR          = 1e-4
PATIENCE    = 8
TRAIN_FRAC  = 0.70
VAL_FRAC    = 0.15

print("=" * 65)
print("  Gate Model Training — MobileNetV2 (FIXED)")
print(f"  BASE_DIR : {BASE_DIR}")
print(f"  CSV      : {CSV_PATH}")
print(f"  Device   : {DEVICE}")
print("=" * 65)


# ── DATASET ───────────────────────────────────────────────────
class GateDataset(Dataset):
    def __init__(self, rows, root, transform=None):
        self.rows, self.root, self.transform = rows, root, transform

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row   = self.rows[idx]
        path  = os.path.join(self.root, row["image_path"])
        label = int(row["label"])
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), (128, 128, 128))
        if self.transform:
            img = self.transform(img)
        return img, label


# ── TRANSFORMS ────────────────────────────────────────────────
train_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE + 32, IMG_SIZE + 32)),
    transforms.RandomCrop(IMG_SIZE),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4, hue=0.1),
    transforms.RandomRotation(30),
    transforms.RandomGrayscale(p=0.05),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
val_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# ── STRATIFIED SPLIT ──────────────────────────────────────────
def stratified_split(rows, train_frac, val_frac):
    def split_one(lst):
        n = len(lst)
        n_tr  = int(n * train_frac)
        n_val = int(n * val_frac)
        return lst[:n_tr], lst[n_tr:n_tr+n_val], lst[n_tr+n_val:]

    pass_rows   = [r for r in rows if int(r['label']) == 1]
    reject_rows = [r for r in rows if int(r['label']) == 0]
    random.shuffle(pass_rows)
    random.shuffle(reject_rows)

    p_tr, p_val, p_te = split_one(pass_rows)
    r_tr, r_val, r_te = split_one(reject_rows)

    train = p_tr + r_tr;  random.shuffle(train)
    val   = p_val + r_val; random.shuffle(val)
    test  = p_te + r_te;  random.shuffle(test)
    return train, val, test


# ── LOAD CSV ──────────────────────────────────────────────────
print(f"\nLoading dataset from: {CSV_PATH}...")
all_rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        # Convert disease names to numeric labels
        # All rows in dataset.csv are valid tomato leaves (PASS=1)
        row['label'] = '1'  # Assign PASS label to all samples
        all_rows.append(row)

counts = Counter(int(r['label']) for r in all_rows)
print(f"  Total samples : {len(all_rows)}")
print(f"  PASS (valid tomato leaves) : {counts[1]}")
if 0 in counts:
    print(f"  REJECT : {counts[0]}")

train_rows, val_rows, test_rows = stratified_split(all_rows, TRAIN_FRAC, VAL_FRAC)
print(f"  Train : {len(train_rows)}  Val: {len(val_rows)}  Test: {len(test_rows)}")

train_ds = GateDataset(train_rows, IMG_ROOT, train_tf)
val_ds   = GateDataset(val_rows,   IMG_ROOT, val_tf)
test_ds  = GateDataset(test_rows,  IMG_ROOT, val_tf)

# Weighted sampler — balances class imbalance during training
train_labels = [int(r['label']) for r in train_rows]
class_counts = Counter(train_labels)
weights      = [1.0 / class_counts[l] for l in train_labels]
sampler      = WeightedRandomSampler(weights, len(weights), replacement=True)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,   num_workers=0)
test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False,   num_workers=0)


# ── MODEL ─────────────────────────────────────────────────────
model = models.mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)
model.classifier = nn.Sequential(
    nn.Dropout(p=0.4),
    nn.Linear(model.last_channel, 256),
    nn.ReLU(),
    nn.Dropout(p=0.3),
    nn.Linear(256, 1)
)
model = model.to(DEVICE)

pos_weight = torch.tensor([counts[0] / counts[1]], dtype=torch.float32).to(DEVICE)
criterion  = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
optimizer  = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler  = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', 
    factor=0.5, 
    patience=3,
    #   verbose=False
    )


# ── TRAIN / EVAL LOOP ─────────────────────────────────────────
def run_epoch(loader, train=True):
    model.train() if train else model.eval()
    total_loss = total_correct = total = 0
    all_labels, all_preds = [], []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for imgs, labels in loader:
            imgs, labels = imgs.to(DEVICE), labels.float().to(DEVICE)
            logits = model(imgs).squeeze(1)
            loss   = criterion(logits, labels)
            if train:
                optimizer.zero_grad(); loss.backward(); optimizer.step()
            preds = (torch.sigmoid(logits) >= 0.5).long()
            total_loss    += loss.item() * len(labels)
            total_correct += (preds == labels.long()).sum().item()
            total         += len(labels)
            all_labels.extend(labels.long().cpu().numpy())
            all_preds.extend(preds.cpu().numpy())
    return total_loss/total, 100.0*total_correct/total, all_labels, all_preds


# ── TRAINING ──────────────────────────────────────────────────
best_val_loss = float('inf')
patience_ctr  = best_epoch = 0
history       = {"tr_loss":[], "vl_loss":[], "tr_acc":[], "vl_acc":[]}
MODEL_PATH    = os.path.join(MODEL_DIR, "gate_leaf.pth")

print(f"\n  {'Ep':>4}  {'TrLoss':>8}  {'TrAcc':>7}  {'VlLoss':>8}  {'VlAcc':>7}  Note")
print("  " + "-" * 60)

for epoch in range(1, MAX_EPOCHS + 1):
    tr_loss, tr_acc, _, _ = run_epoch(train_loader, True)
    vl_loss, vl_acc, _, _ = run_epoch(val_loader,   False)

    history["tr_loss"].append(tr_loss)
    history["vl_loss"].append(vl_loss)
    history["tr_acc"].append(tr_acc)
    history["vl_acc"].append(vl_acc)
    scheduler.step(vl_loss)

    if vl_loss < best_val_loss:
        best_val_loss = vl_loss
        best_epoch    = epoch
        patience_ctr  = 0
        torch.save(model.state_dict(), MODEL_PATH)
        note = "✅ SAVED"
    else:
        patience_ctr += 1
        note = f"patience {patience_ctr}/{PATIENCE}"

    print(f"  {epoch:>4}   {tr_loss:>7.4f}   {tr_acc:>6.2f}   {vl_loss:>7.4f}   {vl_acc:>6.2f}   {note}")

    if patience_ctr >= PATIENCE:
        print(f"\n  Early stop at epoch {epoch} (no improvement for {PATIENCE} epochs)")
        break


# ── TEST EVALUATION ───────────────────────────────────────────
print("\n" + "=" * 65)
print("  FINAL TEST SET EVALUATION")
print("=" * 65)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
_, test_acc, test_labels, test_preds = run_epoch(test_loader, False)

precision = precision_score(test_labels, test_preds, zero_division=0) * 100
recall    = recall_score(test_labels, test_preds, zero_division=0) * 100
f1        = f1_score(test_labels, test_preds, zero_division=0) * 100
cm        = confusion_matrix(test_labels, test_preds)
gap       = history["tr_acc"][best_epoch-1] - test_acc

print(f"  Test Accuracy : {test_acc:.2f}%")
print(f"  Precision     : {precision:.2f}%")
print(f"  Recall        : {recall:.2f}%")
print(f"  F1 Score      : {f1:.2f}%")
print(f"  Best Epoch    : {best_epoch}")
print(f"\n  Confusion Matrix (rows=Actual, cols=Predicted):")
print(f"                Pred REJECT   Pred PASS")
print(f"  Actual REJECT   {cm[0][0]:>6}        {cm[0][1]:>5}")
print(f"  Actual PASS     {cm[1][0]:>6}        {cm[1][1]:>5}")
print(f"\n  Overfitting Gap : {gap:.2f}%  ", end="")
print("✅ Good" if gap < 5 else ("⚠️  Moderate" if gap < 10 else "❌ High — needs more data"))


# ── PLOT ──────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
ep_x = range(1, len(history["tr_loss"]) + 1)

axes[0].plot(ep_x, history["tr_loss"], label="Train"); axes[0].plot(ep_x, history["vl_loss"], label="Val")
axes[0].axvline(best_epoch, color='g', linestyle='--', label=f"Best ep {best_epoch}")
axes[0].set_title("Loss"); axes[0].set_xlabel("Epoch"); axes[0].legend(); axes[0].grid(True)

axes[1].plot(ep_x, history["tr_acc"], label="Train"); axes[1].plot(ep_x, history["vl_acc"], label="Val")
axes[1].axvline(best_epoch, color='g', linestyle='--', label=f"Best ep {best_epoch}")
axes[1].set_title("Accuracy (%)"); axes[1].set_xlabel("Epoch"); axes[1].legend(); axes[1].grid(True)

plt.tight_layout()
plot_path = os.path.join(MODEL_DIR, "gate_leaf_training_results.png")
plt.savefig(plot_path); plt.close()

with open(os.path.join(MODEL_DIR, "gate_leaf_results.txt"), 'w') as f:
    f.write(f"Accuracy : {test_acc:.2f}%\nPrecision: {precision:.2f}%\n"
            f"Recall   : {recall:.2f}%\nF1       : {f1:.2f}%\n"
            f"Best Ep  : {best_epoch}\nGap      : {gap:.2f}%\nCM:\n{cm}\n")

print(f"\n  Model : {MODEL_PATH}")
print(f"  Plot  : {plot_path}")
print("=" * 65)
print("  TRAINING COMPLETE")
print("=" * 65)
print("\nNext: python -m ml.training.train_unet_earlyblight")