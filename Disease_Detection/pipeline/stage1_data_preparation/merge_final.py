# merge_final.py
# Merges three sources into one clean final dataset:
#   Source 1: clean_dataset     (808 EB + 808 LB studio images)
#   Source 2: roboflow_lb       (203 LB field images, idx 1)
#   Source 3: roboflow_eb       (158 EB field images, idx 0)
#
# Output: C:\Users\mfart\Desktop\Research\component03\data\splits\
#
# Run from: C:\Users\mfart\Desktop\Research\component03\pipeline\stage1_data_preparation\
#   python merge_final.py

import random
import shutil
import yaml
from collections import defaultdict
from pathlib import Path
from sklearn.model_selection import train_test_split

random.seed(42)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection")
CLEAN_DIR    = Path(r"C:\tomato_yolo_v2\clean_dataset")
RF_LB_DIR    = BASE / "data" / "annotated" / "roboflow_lb"
RF_EB_DIR    = BASE / "data" / "annotated" / "roboflow_eb"
OUTPUT_DIR   = BASE / "data" / "splits"

CLASS_NAMES  = ["Early_Blight", "Late_Blight"]
IMG_EXTS     = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
SPLITS       = ["train", "valid", "test"]

# Class index mapping per source
# clean_dataset : EB=0, LB=1 (already correct)
# roboflow_lb   : EB=0, LB=1 (already correct)
# roboflow_eb   : EB=0       (only one class)

SOURCE_CONFIG = [
    # (directory, {source_idx: new_idx}, splits_to_scan)
    (CLEAN_DIR, {0: 0, 1: 1}, ["train", "valid", "test"]),
    (RF_LB_DIR, {0: 0, 1: 1}, ["train", "valid", "test"]),
    (RF_EB_DIR, {0: 0},       ["train", "valid", "test"]),
]


# ── Collect all images ────────────────────────────────────────────────────────
def collect_all():
    print("[1] Collecting images from all sources...")
    all_items = []

    for src_dir, idx_map, splits in SOURCE_CONFIG:
        src_count = 0
        for split in splits:
            lbl_dir = src_dir / split / "labels"
            img_dir = src_dir / split / "images"
            if not lbl_dir.exists():
                continue

            for lbl_file in lbl_dir.glob("*.txt"):
                img_path = None
                for ext in IMG_EXTS:
                    candidate = img_dir / (lbl_file.stem + ext)
                    if candidate.exists():
                        img_path = candidate
                        break
                if img_path is None:
                    continue

                # Remap labels
                new_lines = []
                classes_found = set()
                with open(lbl_file) as f:
                    for line in f:
                        parts = line.strip().split()
                        if not parts:
                            continue
                        old_cls = int(parts[0])
                        if old_cls in idx_map:
                            new_cls = idx_map[old_cls]
                            new_lines.append(
                                f"{new_cls} {' '.join(parts[1:])}"
                            )
                            classes_found.add(new_cls)

                if new_lines:
                    all_items.append({
                        "img_path": img_path,
                        "lines":    new_lines,
                        "classes":  classes_found,
                        "source":   src_dir.name,
                    })
                    src_count += 1

        print(f"    {src_dir.name:<20} : {src_count} images")

    print(f"\n    Total collected : {len(all_items)} images")
    return all_items


# ── Show class distribution ───────────────────────────────────────────────────
def show_distribution(items, label=""):
    counts = defaultdict(int)
    images = defaultdict(int)
    for item in items:
        seen = set()
        for line in item["lines"]:
            cls = int(line.split()[0])
            counts[cls] += 1
            seen.add(cls)
        for c in seen:
            images[c] += 1

    if label:
        print(f"\n    {label}")
    for i, name in enumerate(CLASS_NAMES):
        print(f"      {name:<15} : {images[i]:>4} images  {counts[i]:>6} boxes")


# ── Write split ───────────────────────────────────────────────────────────────
def write_split(items, split_name):
    img_out = OUTPUT_DIR / split_name / "images"
    lbl_out = OUTPUT_DIR / split_name / "labels"
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)

    for item in items:
        img_src = item["img_path"]
        lines   = item["lines"]

        dest_img = img_out / img_src.name
        dest_lbl = lbl_out / (img_src.stem + ".txt")

        counter = 1
        while dest_img.exists():
            dest_img = img_out / f"{img_src.stem}_{counter}{img_src.suffix}"
            dest_lbl = lbl_out / f"{img_src.stem}_{counter}.txt"
            counter += 1

        shutil.copy2(img_src, dest_img)
        with open(dest_lbl, "w") as f:
            f.write("\n".join(lines) + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("Final Dataset Merge")
    print("=" * 55)

    # Collect
    all_items = collect_all()
    show_distribution(all_items, "Overall distribution:")

    # Deduplicate by filename
    seen_names = set()
    unique_items = []
    for item in all_items:
        name = item["img_path"].name
        if name not in seen_names:
            seen_names.add(name)
            unique_items.append(item)

    print(f"\n    After deduplication : {len(unique_items)} images")
    random.shuffle(unique_items)

    # Split 70/15/15
    train_items, temp       = train_test_split(unique_items, test_size=0.30, random_state=42)
    valid_items, test_items = train_test_split(temp,         test_size=0.50, random_state=42)

    print(f"\n[2] Splitting 70/15/15...")
    print(f"    Train : {len(train_items)}")
    print(f"    Valid : {len(valid_items)}")
    print(f"    Test  : {len(test_items)}")

    # Show per-split distribution
    show_distribution(train_items, "Train distribution:")
    show_distribution(valid_items, "Valid distribution:")
    show_distribution(test_items,  "Test  distribution:")

    # Write files
    print("\n[3] Writing files...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    write_split(train_items, "train")
    write_split(valid_items, "valid")
    write_split(test_items,  "test")

    # Write data.yaml
    yaml_cfg = {
        "path":  str(OUTPUT_DIR.resolve()),
        "train": "train/images",
        "val":   "valid/images",
        "test":  "test/images",
        "nc":    len(CLASS_NAMES),
        "names": CLASS_NAMES,
    }
    yaml_path = OUTPUT_DIR / "data.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(yaml_cfg, f, default_flow_style=False, sort_keys=False)

    print("\n" + "=" * 55)
    print("Merge Complete")
    print("=" * 55)
    print(f"  Output    : {OUTPUT_DIR}")
    print(f"  data.yaml : {yaml_path}")
    print(f"  Train     : {len(train_items)}")
    print(f"  Valid     : {len(valid_items)}")
    print(f"  Test      : {len(test_items)}")
    print(f"  Total     : {len(unique_items)}")
    print("\nNext: run stage2_model_training\\train_final.py")


if __name__ == "__main__":
    main()
