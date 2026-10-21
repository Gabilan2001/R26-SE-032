"""
train_leaf_validator.py
=======================
Trains a 3-class EfficientNet-B0 classifier:
  Class 0 -> tomato_leaf       (all tomato leaf types)
  Class 1 -> other_plant_leaf  (other crop species -- PlantVillage, non-tomato)
  Class 2 -> random_object     (not a plant at all -- CIFAR-100 + the
                                 original Intel landscape scenes)

Was a binary tomato-vs-not classifier. Went 3-class because the old
negative class (Intel landscape scenes only) had never seen "a leaf, but
the wrong species" or "a close-up food/object photo" -- confirmed in real
testing: a potato late-blight photo and a cake photo both slipped straight
through as "tomato leaf". Splitting the negative side into these two real
failure modes also lets the app give a much better error message --
"that's a different plant's leaf" vs. "that's not a leaf at all" -- instead
of one generic "not a tomato leaf".

See fetch_negative_class_data.py for how other_plant_leaf/ and
random_object/'s CIFAR-100 portion were sourced.

Output:
  leaf_validator.pth  -> saved to models folder

Run from stage4_inference folder:
  python train_leaf_validator.py
"""

import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
OUT_MODEL  = BASE / "models" / "leaf_validator.pth"
NEGATIVES  = BASE / "data" / "leaf_validator_negatives"

CLASS_NAMES = ["tomato_leaf", "other_plant_leaf", "random_object"]

# Class 0: tomato leaf. Field-style (real photos, your own YOLO training
# set) and lab-style (PlantVillage) sources are split out and given an
# EXPLICIT quota each, rather than one flat random draw across both pools
# combined. The lab pool (~9300 images) vastly outnumbers the field pool
# (~1930), so a flat random sample diluted field-style tomato photos down to
# ~17% of the class while other_plant_leaf (below) ended up ~39% field-style
# after its own retrain -- the model could still partly shortcut on
# photography style, just flipped: a real field-condition tomato photo (e.g.
# a leaf-miner-damaged leaf) started getting rejected as "not tomato" at
# 0.21 confidence. Matching the field/lab ratio between classes removes that
# shortcut instead of just relocating it.
TOMATO_FIELD_DIR = BASE / "data" / "splits" / "train" / "images"  # your own YOLO training images
TOMATO_FIELD_TARGET = 800  # ~= other_plant_leaf's field-style share (2000 * 1759/4521 ~= 780)
TOMATO_LAB_DIRS = [
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_healthy"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Early_blight"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Late_blight") if Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Late_blight").exists() else
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\test\Tomato_Late_blight"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Bacterial_spot"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_Septoria_leaf_spot"),
    Path(r"C:\Users\mfart\Desktop\Models\tomato-disease\data\train\Tomato_YellowLeaf_Curl_Virus"),
]

# Class 1: other plant species' leaves -- one subfolder per species/disease
# category, discovered at runtime. Two sources mixed together on purpose:
# PlantVillage (lab/studio-style crops) AND PlantDoc (real field-condition
# photos -- messy backgrounds, natural lighting). Lab-only negatives let the
# model shortcut on "photography style" instead of real leaf morphology,
# since the tomato_leaf class also includes real field photos -- confirmed
# in testing: real potato leaf photos got misclassified as tomato_leaf with
# 0.97-1.00 confidence. Mixing both styles into the negative class forces it
# to actually learn leaf differences instead of background/lighting cues.
def _leaf_subdirs(folder_name):
    d = NEGATIVES / folder_name
    return sorted(p for p in d.glob("*") if p.is_dir()) if d.exists() else []

OTHER_LEAF_DIRS = _leaf_subdirs("other_plant_leaves") + _leaf_subdirs("other_plant_leaves_field")

# Class 2: not a plant at all -- Food-101 real photos (full-resolution;
# replaced CIFAR-100's native 32x32 thumbnails, which were blurry enough
# after upscaling to 224x224 that the model could shortcut on "blurry =
# random_object" instead of "this is a mundane object" -- wouldn't have
# generalized to a real sharp photo like the cake photo that originally
# slipped through), plus the original Intel landscape scenes.
RANDOM_OBJECT_DIRS = [
    NEGATIVES / "random_objects",
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\buildings"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\forest"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\glacier"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\mountain"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\sea"),
    Path(r"C:\Users\mfart\Downloads\Compressed\archive\seg_train\seg_train\street"),
]

# ── Config ────────────────────────────────────────────────────────────────────
TOMATO_LIMIT       = 2000  # max images per class -- kept roughly balanced
OTHER_LEAF_LIMIT    = 2000
RANDOM_OBJECT_LIMIT = 2000
VAL_SPLIT       = 0.2
IMG_SIZE        = 224
BATCH_SIZE      = 32
EPOCHS          = 15
LR              = 1e-4
THRESHOLD       = 0.5     # confidence to confirm tomato leaf -- keep in sync with
# VALIDATOR_THRESHOLD in app.py / app_mobile.py (this constant itself isn't
# used at inference time, it's just documentation of the deployed value)

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
        print(f"  {d.name:<45} {len(imgs)} images")

    random.shuffle(all_imgs)
    return all_imgs[:limit]


# ── Build model ───────────────────────────────────────────────────────────────
def build_model():
    m = models.efficientnet_b0(weights="IMAGENET1K_V1")
    m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(CLASS_NAMES))
    return m.to(device)


# ── Train ─────────────────────────────────────────────────────────────────────
def train():
    random.seed(42)
    torch.manual_seed(42)

    print("=" * 55)
    print("Leaf Validator — 3-Class Classifier Training")
    print("=" * 55)
    print(f"  Device : {device}")

    # Collect images
    print("\n  Collecting tomato leaf images...")
    tomato_field_imgs = collect_images([TOMATO_FIELD_DIR], TOMATO_FIELD_TARGET)
    tomato_lab_imgs = collect_images(TOMATO_LAB_DIRS, TOMATO_LIMIT - len(tomato_field_imgs))
    tomato_imgs = tomato_field_imgs + tomato_lab_imgs
    random.shuffle(tomato_imgs)
    print(f"  Total tomato leaf     : {len(tomato_imgs)} "
          f"({len(tomato_field_imgs)} field-style, {len(tomato_lab_imgs)} lab-style)")

    print("\n  Collecting other-plant-leaf images...")
    other_leaf_imgs = collect_images(OTHER_LEAF_DIRS, OTHER_LEAF_LIMIT)
    print(f"  Total other plant leaf: {len(other_leaf_imgs)}")

    print("\n  Collecting random-object images...")
    random_obj_imgs = collect_images(RANDOM_OBJECT_DIRS, RANDOM_OBJECT_LIMIT)
    print(f"  Total random object   : {len(random_obj_imgs)}")

    # Build samples
    samples = (
        [(p, 0) for p in tomato_imgs] +
        [(p, 1) for p in other_leaf_imgs] +
        [(p, 2) for p in random_obj_imgs]
    )
    random.shuffle(samples)

    print(f"\n  Total samples      : {len(samples)}")
    for idx, name in enumerate(CLASS_NAMES):
        print(f"  {name:<20}  (class {idx}) : {sum(1 for _, l in samples if l == idx)}")

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
                "classes"         : CLASS_NAMES,
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
    print(classification_report(all_labels, all_preds, target_names=CLASS_NAMES))

    cm = confusion_matrix(all_labels, all_preds)
    print("  Confusion Matrix:")
    header = "".join(f"{'Pred ' + n:>20}" for n in CLASS_NAMES)
    print(f"  {'':<20}{header}")
    for i, name in enumerate(CLASS_NAMES):
        row = "".join(f"{cm[i][j]:>20}" for j in range(len(CLASS_NAMES)))
        print(f"  GT {name:<17}{row}")

    print("\n  Training complete ✅")
    print("=" * 55)


if __name__ == "__main__":
    train()
