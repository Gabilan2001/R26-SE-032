"""
Real evaluation of the saved leaf_validator.pth checkpoint.
Reproduces the EXACT data collection + train/val split logic from
train_leaf_validator.py (same seed, same directories, same order) so the
val set evaluated here matches the held-out set the checkpoint was actually
selected on -- verified below by checking computed accuracy against the
checkpoint's own stored best_val_acc.
"""
import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix

BASE       = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
OUT_MODEL  = BASE / "models" / "leaf_validator.pth"
NEGATIVES  = BASE / "data" / "leaf_validator_negatives"
CLASS_NAMES = ["tomato_leaf", "other_plant_leaf", "random_object"]

TOMATO_FIELD_DIR = BASE / "data" / "splits" / "train" / "images"
TOMATO_FIELD_TARGET = 800
TOMATO_LAB_DIRS = [
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_healthy"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Early_blight"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Late_blight") if Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Late_blight").exists() else
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\test\Tomato_Late_blight"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Bacterial_spot"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Septoria_leaf_spot"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_YellowLeaf_Curl_Virus"),
]

def _leaf_subdirs(folder_name):
    d = NEGATIVES / folder_name
    return sorted(p for p in d.glob("*") if p.is_dir()) if d.exists() else []

OTHER_LEAF_DIRS = _leaf_subdirs("other_plant_leaves") + _leaf_subdirs("other_plant_leaves_field")

RANDOM_OBJECT_DIRS = [
    NEGATIVES / "random_objects",
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\buildings"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\forest"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\glacier"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\mountain"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\sea"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\street"),
]

TOMATO_LIMIT = 2000
OTHER_LEAF_LIMIT = 2000
RANDOM_OBJECT_LIMIT = 2000
VAL_SPLIT = 0.2
IMG_SIZE = 224
BATCH_SIZE = 32
THRESHOLD = 0.5

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

VAL_TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

class LeafDataset(Dataset):
    def __init__(self, samples, transform):
        self.samples = samples
        self.transform = transform
    def __len__(self):
        return len(self.samples)
    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            img = Image.open(path).convert("RGB")
            img = self.transform(img)
        except Exception:
            img = torch.zeros(3, IMG_SIZE, IMG_SIZE)
        return img, label

def collect_images(dirs, limit):
    exts = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
    all_imgs = []
    for d in dirs:
        if not d.exists():
            print(f"  Warning: {d} not found - skipping")
            continue
        imgs = [p for p in d.iterdir() if p.suffix in exts]
        all_imgs.extend(imgs)
    random.shuffle(all_imgs)
    return all_imgs[:limit]

def main():
    random.seed(42)
    torch.manual_seed(42)

    tomato_field_imgs = collect_images([TOMATO_FIELD_DIR], TOMATO_FIELD_TARGET)
    tomato_lab_imgs = collect_images(TOMATO_LAB_DIRS, TOMATO_LIMIT - len(tomato_field_imgs))
    tomato_imgs = tomato_field_imgs + tomato_lab_imgs
    random.shuffle(tomato_imgs)

    other_leaf_imgs = collect_images(OTHER_LEAF_DIRS, OTHER_LEAF_LIMIT)
    random_obj_imgs = collect_images(RANDOM_OBJECT_DIRS, RANDOM_OBJECT_LIMIT)

    samples = (
        [(p, 0) for p in tomato_imgs] +
        [(p, 1) for p in other_leaf_imgs] +
        [(p, 2) for p in random_obj_imgs]
    )
    random.shuffle(samples)

    split = int(len(samples) * (1 - VAL_SPLIT))
    val_samples = samples[split:]
    print(f"Total samples: {len(samples)}  Val samples: {len(val_samples)}")
    for idx, name in enumerate(CLASS_NAMES):
        print(f"  val {name}: {sum(1 for _, l in val_samples if l == idx)}")

    val_ds = LeafDataset(val_samples, VAL_TRANSFORM)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    ckpt = torch.load(str(OUT_MODEL), map_location=device, weights_only=False)
    print(f"\nCheckpoint stored best_val_acc: {ckpt['best_val_acc']:.4f}")
    print(f"Checkpoint classes: {ckpt['classes']}")

    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(CLASS_NAMES))
    model.load_state_dict(ckpt["model_state_dict"])
    model = model.to(device)
    model.eval()

    all_preds, all_labels, all_probs = [], [], []
    with torch.no_grad():
        for imgs, labels in val_loader:
            imgs = imgs.to(device)
            out = model(imgs)
            probs = torch.softmax(out, dim=1).cpu().numpy()
            preds = out.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy())
            all_probs.extend(probs)

    acc = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_labels)
    print(f"\nRecomputed val accuracy on this split: {acc:.4f}")
    print(f"Matches checkpoint's stored best_val_acc: {abs(acc - ckpt['best_val_acc']) < 1e-6}")

    print("\nClassification Report:")
    print(classification_report(all_labels, all_preds, target_names=CLASS_NAMES, digits=4))

    cm = confusion_matrix(all_labels, all_preds)
    print("Confusion Matrix (rows=true, cols=predicted):")
    header = "".join(f"{'Pred_' + n:>20}" for n in CLASS_NAMES)
    print(f"{'':<22}{header}")
    for i, name in enumerate(CLASS_NAMES):
        row = "".join(f"{cm[i][j]:>20}" for j in range(len(CLASS_NAMES)))
        print(f"True_{name:<17}{row}")

    # False Acceptance Rate: negative classes (other_plant_leaf=1, random_object=2)
    # wrongly predicted as tomato_leaf=0
    neg_total = sum(1 for l in all_labels if l != 0)
    neg_accepted_as_tomato = sum(1 for p, l in zip(all_preds, all_labels) if l != 0 and p == 0)
    far = neg_accepted_as_tomato / neg_total if neg_total else 0.0
    print(f"\nFalse Acceptance Rate (non-tomato predicted as tomato_leaf): {neg_accepted_as_tomato}/{neg_total} = {far:.4f}")

    # Per-negative-class breakdown
    for cls_idx, cls_name in [(1, "other_plant_leaf"), (2, "random_object")]:
        cls_total = sum(1 for l in all_labels if l == cls_idx)
        cls_accepted = sum(1 for p, l in zip(all_preds, all_labels) if l == cls_idx and p == 0)
        print(f"  {cls_name} accepted as tomato_leaf: {cls_accepted}/{cls_total} = {(cls_accepted/cls_total if cls_total else 0):.4f}")

if __name__ == "__main__":
    main()
