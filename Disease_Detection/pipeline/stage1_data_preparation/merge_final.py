# merge_final.py
# Builds the final 4-class dataset (Early_Blight, Late_Blight, Healthy, Leaf_Miner):
#   Source 1: tomato_leaf_1        (native 640x640 Roboflow export)
#             -> Early_Blight, Late_Blight, Healthy
#   Source 2: leaf_miner_symptom   (curated Roboflow export, 233 unique source photos)
#             -> Leaf_Miner, plus any co-occurring Early_Blight/Late_Blight boxes
#             in the same image
#
# Supersedes the earlier 2-class-only version of this script (studio + field
# EB/LB images only). Replaced once the 4-class model was validated as the
# project's final result -- see stage2/stage3 for the corresponding training
# and evaluation scripts, and the project's held-out test metrics for why
# native-resolution tomato_leaf_1 was chosen over other candidate sources for
# Early_Blight/Late_Blight/Healthy (some alternative sources had annotation
# quality issues -- inconsistent box sizes, some near-whole-image boxes --
# that inflated benchmark scores without improving real detection quality).
#
# Every source photo is deduplicated by base filename (stripping Roboflow's
# .rf.<hash> augmentation suffix) so no near-duplicate of the same original
# image can land in more than one split -- this applies even though neither
# source here turned out to have duplicate augmented copies, kept as a
# defensive check for future dataset swaps.
#
# Output: <repo>\Disease_Detection\data\splits\
#
# Run from: <repo>\Disease_Detection\pipeline\stage1_data_preparation\
#   python merge_final.py

import os
import re
import random
import shutil
import yaml
from collections import defaultdict, Counter
from pathlib import Path

random.seed(42)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE          = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
TL1_DIR       = BASE / "data" / "annotated" / "tomato_leaf_1"       # native 640px, EB/LB/Healthy
LM_DIR        = BASE / "data" / "annotated" / "leaf_miner_symptom"  # curated, Leaf_Miner
OUTPUT_DIR    = BASE / "data" / "splits"

CLASS_NAMES   = ["Early_Blight", "Late_Blight", "Healthy", "Leaf_Miner"]
RATIOS        = {"train": 0.8, "val": 0.1, "test": 0.1}

# tomato_leaf_1 (nc=5): 0=Early_blight,1=Late_blight,2=Leaf_Mold,3=Septoria_leaf_spot,4=healthy
TL1_KEEP_MAP  = {0: 0, 1: 1, 4: 2}
# leaf_miner_symptom (nc=3): 0=Early Blight,1=Late Blight,2=Leaf_Miner
LM_KEEP_MAP   = {0: 0, 1: 1, 2: 3}

SPLITS        = ["train", "valid", "test"]  # source folder names (Roboflow convention)


def base_key(fname: str) -> str:
    name = re.sub(r'\.(jpg|jpeg|png)$', '', fname, flags=re.I)
    name = re.sub(r'\.rf\.[0-9a-f]+$', '', name, flags=re.I)
    return name


# ── Collect + dedupe + class-filter one source ────────────────────────────────
def collect_source(src_dir, keep_map, require_class=None):
    groups = {}
    for split in SPLITS:
        img_dir = src_dir / split / "images"
        lbl_dir = src_dir / split / "labels"
        if not img_dir.exists():
            continue
        for fname in sorted(os.listdir(img_dir)):
            stem = Path(fname).stem
            lbl_path = lbl_dir / (stem + ".txt")
            if not lbl_path.exists():
                continue
            with open(lbl_path) as fh:
                lines = [l.strip() for l in fh if l.strip()]
            kept_lines, target_classes = [], set()
            for l in lines:
                parts = l.split()
                old_cid = int(parts[0])
                if old_cid not in keep_map:
                    continue
                new_cid = keep_map[old_cid]
                parts[0] = str(new_cid)
                kept_lines.append(" ".join(parts))
                target_classes.add(new_cid)
            if not kept_lines:
                continue
            if require_class is not None and require_class not in target_classes:
                continue
            key = base_key(fname)
            if key in groups:
                continue  # dedup: one real copy per source photo
            groups[key] = {
                "img_path": img_dir / fname,
                "lines": kept_lines,
                "classes": target_classes,
            }
    return groups


# ── Show class distribution ───────────────────────────────────────────────────
def show_distribution(groups_by_key, label=""):
    images = Counter()
    boxes = Counter()
    for g in groups_by_key.values():
        for c in g["classes"]:
            images[c] += 1
        for l in g["lines"]:
            boxes[int(l.split()[0])] += 1
    if label:
        print(f"\n    {label}")
    for i, name in enumerate(CLASS_NAMES):
        print(f"      {name:<15} : {images[i]:>4} images  {boxes[i]:>6} boxes")


# ── Write split ───────────────────────────────────────────────────────────────
def write_split(groups, split_name):
    img_out = OUTPUT_DIR / split_name / "images"
    lbl_out = OUTPUT_DIR / split_name / "labels"
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)
    for g in groups:
        img_src = g["img_path"]
        shutil.copy2(img_src, img_out / img_src.name)
        with open(lbl_out / (img_src.stem + ".txt"), "w") as f:
            f.write("\n".join(g["lines"]) + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("Final Dataset Merge -- 4-Class (EB / LB / Healthy / Leaf_Miner)")
    print("=" * 55)

    print("\n[1] Collecting images from all sources...")
    tl1_groups = collect_source(TL1_DIR, TL1_KEEP_MAP)
    lm_groups = collect_source(LM_DIR, LM_KEEP_MAP, require_class=3)
    print(f"    {'tomato_leaf_1':<20} : {len(tl1_groups)} images (EB/LB/Healthy)")
    print(f"    {'leaf_miner_symptom':<20} : {len(lm_groups)} images (Leaf_Miner, + co-occurring EB/LB)")

    all_groups = {}
    for k, v in tl1_groups.items():
        all_groups[f"tl1_{k}"] = v
    for k, v in lm_groups.items():
        all_groups[f"lm_{k}"] = v
    print(f"\n    Total unique images : {len(all_groups)}")
    show_distribution(all_groups, "Overall distribution:")

    # Stratified 80/10/10 split at the group level, bucketed by the rarest
    # class present in each image (protects minority-class split ratios for
    # any image that happens to contain more than one target class).
    class_freq = Counter()
    for g in all_groups.values():
        for c in g["classes"]:
            class_freq[c] += 1

    by_bucket = defaultdict(list)
    for key, g in all_groups.items():
        rarest = min(g["classes"], key=lambda c: class_freq[c])
        by_bucket[rarest].append(key)

    split_assignment = {"train": [], "val": [], "test": []}
    for cid in sorted(by_bucket.keys()):
        keys = by_bucket[cid]
        random.shuffle(keys)
        n = len(keys)
        n_train = round(n * RATIOS["train"])
        n_val = round(n * RATIOS["val"])
        split_assignment["train"].extend(keys[:n_train])
        split_assignment["val"].extend(keys[n_train:n_train + n_val])
        split_assignment["test"].extend(keys[n_train + n_val:])

    print(f"\n[2] Splitting 80/10/10 (stratified per class)...")
    print(f"    Train : {len(split_assignment['train'])}")
    print(f"    Valid : {len(split_assignment['val'])}")
    print(f"    Test  : {len(split_assignment['test'])}")

    train_groups = [all_groups[k] for k in split_assignment["train"]]
    val_groups = [all_groups[k] for k in split_assignment["val"]]
    test_groups = [all_groups[k] for k in split_assignment["test"]]

    show_distribution({k: all_groups[k] for k in split_assignment["train"]}, "Train distribution:")
    show_distribution({k: all_groups[k] for k in split_assignment["val"]}, "Valid distribution:")
    show_distribution({k: all_groups[k] for k in split_assignment["test"]}, "Test  distribution:")

    # Write files
    print("\n[3] Writing files...")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    write_split(train_groups, "train")
    write_split(val_groups, "valid")
    write_split(test_groups, "test")

    # Write data.yaml
    yaml_cfg = {
        "path": str(OUTPUT_DIR.resolve()),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": len(CLASS_NAMES),
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
    print(f"  Train     : {len(train_groups)}")
    print(f"  Valid     : {len(val_groups)}")
    print(f"  Test      : {len(test_groups)}")
    print(f"  Total     : {len(all_groups)}")
    print("\nNext: run stage2_model_training\\train_final.py")


if __name__ == "__main__":
    main()
