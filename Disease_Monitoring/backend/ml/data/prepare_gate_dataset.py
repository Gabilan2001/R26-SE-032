"""
Gate Dataset Preparation — FIXED VERSION
Realistic REJECT images for Gate Model training
"""

import os
import csv
import random
import cv2
import numpy as np

# ── PATHS ────────────────────────────────────────────────────
# __file__ = Monitoring/ml/data/prepare_gate_dataset.py
# go up 2 levels → Monitoring/
BASE_DIR   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PV_PATH    = os.path.join(BASE_DIR, "datasets", "PlantVillage")
REJECT_DIR = os.path.join(PV_PATH, "REJECT")
CSV_OUT    = os.path.join(BASE_DIR, "datasets", "leaf_disease", "gate_dataset.csv")

os.makedirs(REJECT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)

IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')

print("=" * 60)
print("GATE DATASET PREPARATION — FIXED")
print(f"BASE_DIR : {BASE_DIR}")
print(f"PV_PATH  : {PV_PATH}")
print(f"CSV_OUT  : {CSV_OUT}")
print("=" * 60)

# ── STEP 1: Scan PASS images ──────────────────────────────────
rows       = []
all_images = []

for folder_name in sorted(os.listdir(PV_PATH)):
    folder_path = os.path.join(PV_PATH, folder_name)
    if not os.path.isdir(folder_path) or folder_name == "REJECT":
        continue
    images = [f for f in os.listdir(folder_path) if f.endswith(IMAGE_EXTS)]
    for img_file in images:
        full_path = os.path.join(folder_path, img_file)
        rel_path  = os.path.join("datasets", "PlantVillage", folder_name, img_file)
        rows.append({"image_path": rel_path, "disease_name": folder_name,
                     "label": 1, "label_name": "PASS"})
        all_images.append(full_path)
    print(f"  {folder_name}: {len(images)} images → PASS")

print(f"\nTotal PASS images: {len(rows)}")

if len(rows) == 0:
    print(f"\nERROR: No images found in: {PV_PATH}")
    exit(1)

# ── STEP 2: Create REALISTIC REJECT images ───────────────────
# These simulate what farmers actually upload wrongly.
# Subtle enough to require real visual features — not extreme noise/black.

random.shuffle(all_images)
target_reject = int(len(all_images) * 0.45)
to_distort    = all_images[:target_reject]

def make_reject(img, method):
    h, w = img.shape[:2]

    if method == "heavy_occlusion":
        # Simulate thumb/finger covering most of leaf
        result = img.copy()
        skin   = (random.randint(80,180), random.randint(60,140), random.randint(40,120))
        mask   = np.zeros((h, w), dtype=np.uint8)
        pts    = np.array([
            [random.randint(0, w//3), 0],
            [random.randint(2*w//3, w), 0],
            [w, random.randint(0, h//2)],
            [w, h], [0, h],
            [0, random.randint(0, h//2)],
        ], dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        result[mask > 0] = skin
        return result

    elif method == "wrong_crop":
        # Tiny sliver of leaf, rest is soil-coloured background
        crop_h = random.randint(h//10, h//5)
        crop_w = random.randint(w//10, w//5)
        y1 = random.randint(0, h - crop_h)
        x1 = random.randint(0, w - crop_w)
        tiny   = img[y1:y1+crop_h, x1:x1+crop_w]
        result = np.full_like(img, fill_value=(45, 65, 30))
        py = random.randint(0, h - crop_h)
        px = random.randint(0, w - crop_w)
        result[py:py+crop_h, px:px+crop_w] = tiny
        return result

    elif method == "soil_background":
        # Mostly soil texture with tiny leaf patch
        result = np.random.randint(30, 100, img.shape, dtype=np.uint8)
        ph, pw = h//5, w//5
        py = random.randint(0, h - ph)
        px = random.randint(0, w - pw)
        result[py:py+ph, px:px+pw] = img[py:py+ph, px:px+pw]
        return result

    elif method == "motion_blur":
        # Realistic camera shake — not extreme
        size   = random.choice([21, 31, 41])
        angle  = random.uniform(0, 360)
        kernel = np.zeros((size, size))
        kernel[size//2, :] = np.ones(size)
        M      = cv2.getRotationMatrix2D((size//2, size//2), angle, 1.0)
        kernel = cv2.warpAffine(kernel, M, (size, size))
        kernel /= kernel.sum()
        return cv2.filter2D(img, -1, kernel)

    elif method == "wrong_object":
        # Non-plant object colour (tool/plastic/wood)
        colours = [(200,200,200), (150,100,50), (50,50,200), (200,200,50)]
        colour  = random.choice(colours)
        noise   = np.random.randint(-20, 20, img.shape, dtype=np.int16)
        base    = np.clip(np.full_like(img, colour, dtype=np.int16) + noise, 0, 255).astype(np.uint8)
        alpha   = random.uniform(0.7, 0.9)
        return cv2.addWeighted(base, alpha, img, 1-alpha, 0)

    elif method == "extreme_angle":
        # Photo taken at steep angle — perspective warp
        src_pts = np.float32([[0,0],[w,0],[w,h],[0,h]])
        shift   = random.randint(w//3, w//2)
        dst_pts = np.float32([[shift,0],[w,0],[w-shift,h],[0,h]])
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        return cv2.warpPerspective(img, M, (w, h))

    elif method == "out_of_focus":
        # Soft blur — not extreme
        k = random.choice([51, 71, 91])
        return cv2.GaussianBlur(img, (k, k), 0)

    return img


METHODS = ["heavy_occlusion", "wrong_crop", "soil_background",
           "motion_blur", "wrong_object", "extreme_angle", "out_of_focus"]

created = 0
for i, src_path in enumerate(to_distort):
    img = cv2.imread(src_path)
    if img is None:
        continue
    method    = METHODS[i % len(METHODS)]
    result    = make_reject(img, method)
    name      = f"reject_{i:05d}_{method}.png"
    save_path = os.path.join(REJECT_DIR, name)
    cv2.imwrite(save_path, result)
    rel_path  = os.path.join("datasets", "PlantVillage", "REJECT", name)
    rows.append({"image_path": rel_path, "disease_name": "NON_TOMATO",
                 "label": 0, "label_name": "REJECT"})
    created += 1

print(f"REJECT images created: {created}")

# ── STEP 3: Stratified shuffle and save CSV ───────────────────
pass_rows   = [r for r in rows if r['label'] == 1]
reject_rows = [r for r in rows if r['label'] == 0]
random.shuffle(pass_rows)
random.shuffle(reject_rows)

# Interleave so both classes appear throughout the CSV
final_rows = []
for p, r in zip(pass_rows, reject_rows):
    final_rows.append(p)
    final_rows.append(r)
final_rows.extend(pass_rows[len(reject_rows):])

with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["image_path","disease_name","label","label_name"])
    writer.writeheader()
    writer.writerows(final_rows)

print("\n" + "=" * 60)
print("COMPLETE")
print(f"  PASS   (1): {len(pass_rows)}")
print(f"  REJECT (0): {len(reject_rows)}")
print(f"  Total     : {len(final_rows)}")
print(f"  CSV saved : {CSV_OUT}")
print("=" * 60)
print("\nNext: python -m ml.training.train_gate_leaf")