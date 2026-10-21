# fetch_negative_class_data.py
# Prep step for retraining leaf_validator.pth (see train_leaf_validator.py).
#
# Downloads two new negative-class ("not a tomato leaf") sources that the
# original training data (Intel Image Classification: buildings/forest/
# glacier/mountain/sea/street) never covered:
#
#   1. other_plant_leaves/ -- other crop species from PlantVillage's public
#      GitHub mirror (spMohanty/PlantVillage-Dataset, CC0/public dataset).
#      Tomato and potato/pepper are all Solanaceae with visually similar
#      compound leaf shape -- the original validator had ZERO examples of
#      "a leaf, but the wrong species" and let a potato late-blight photo
#      straight through as if it were tomato. Potato + Pepper are weighted
#      heaviest (closest relatives, and the exact reported failure case);
#      ~20 other species folders are sampled lighter for general diversity.
#
#   2. random_objects/ -- CIFAR-100 (Krizhevsky, public dataset, official
#      University of Toronto mirror), covering 100 everyday categories
#      (food, household objects, animals, vehicles, people, ...). The
#      original validator had never seen a close-up food/object photo --
#      only wide outdoor landscapes -- which is why an uploaded cake photo
#      got misread as "tomato leaf" (it resembles the close-up macro
#      composition of the leaf photos far more than a mountain or a street).
#
# This script only fetches and organizes data -- it does NOT modify or run
# train_leaf_validator.py. Run that separately, later, once this data (and
# the script's TOMATO_DIRS / NOT_TOMATO_DIRS) has been reviewed.
#
# Run from stage4_inference folder:
#   python fetch_negative_class_data.py

import json
import random
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
OUT_DIR = BASE / "data" / "leaf_validator_negatives"
LEAVES_DIR = OUT_DIR / "other_plant_leaves"
FIELD_LEAVES_DIR = OUT_DIR / "other_plant_leaves_field"
OBJECTS_DIR = OUT_DIR / "random_objects"

GITHUB_API = "https://api.github.com/repos/spMohanty/PlantVillage-Dataset/contents/raw/color"
RAW_BASE = "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color"

# PlantDoc -- real-world/field-condition photos (scraped from the wild:
# messy backgrounds, natural lighting, varied angles), unlike PlantVillage's
# uniform lab/studio-style crops. The retrained validator confidently (0.97-
# 1.00) misclassified real field photos of potato leaves as tomato_leaf --
# because every other_plant_leaf example it had ever seen was a clean studio
# photo, it could shortcut on "photography style" instead of actual leaf
# morphology, since the tomato_leaf class also included real field photos.
# This adds a same-style negative counterpart so that shortcut stops working.
PLANTDOC_TREE_API = "https://api.github.com/repos/pratikkayal/PlantDoc-Dataset/git/trees/master?recursive=1"
PLANTDOC_RAW_BASE = "https://raw.githubusercontent.com/pratikkayal/PlantDoc-Dataset/master"

# Heaviest weight: closest relatives to tomato (Solanaceae) + the exact
# species that slipped through in testing (potato, late blight).
HEAVY_CATEGORIES = {
    "Potato___Early_blight": 250,
    "Potato___Late_blight": 250,
    "Potato___healthy": 250,
    "Pepper,_bell___Bacterial_spot": 250,
    "Pepper,_bell___healthy": 250,
}
# Lighter sample from every other non-tomato species, just for general
# "leaf-shaped but wrong species" diversity.
LIGHT_PER_CATEGORY = 70

REQUEST_HEADERS = {"User-Agent": "tomatodoc-leaf-validator-data-prep"}


def http_get_json(url):
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_file(url, dest_path):
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        dest_path.write_bytes(resp.read())


def fetch_plantvillage():
    print("=" * 55)
    print("Fetching other_plant_leaves/ from PlantVillage (GitHub)")
    print("=" * 55)

    categories = http_get_json(GITHUB_API)
    all_names = [c["name"] for c in categories if c["type"] == "dir"]
    non_tomato = [n for n in all_names if not n.startswith("Tomato___")]
    print(f"  {len(non_tomato)} non-tomato species/disease categories found")

    for category in non_tomato:
        limit = HEAVY_CATEGORIES.get(category, LIGHT_PER_CATEGORY)
        safe_name = category.replace(",", "").replace(" ", "_").replace("(", "").replace(")", "")
        cat_dir = LEAVES_DIR / safe_name
        cat_dir.mkdir(parents=True, exist_ok=True)

        already = list(cat_dir.glob("*.jpg")) + list(cat_dir.glob("*.JPG"))
        if len(already) >= limit:
            print(f"  {category:<55} already have {len(already)}, skipping")
            continue

        try:
            files = http_get_json(f"{GITHUB_API.rsplit('/color', 1)[0]}/color/{urllib.parse.quote(category)}")
        except Exception as e:
            print(f"  {category:<55} FAILED to list: {e}")
            continue

        image_files = [f["name"] for f in files if f["type"] == "file"]
        random.seed(42)
        random.shuffle(image_files)
        sample = image_files[:limit]

        got = 0
        for fname in sample:
            dest = cat_dir / fname
            if dest.exists():
                got += 1
                continue
            url = f"{RAW_BASE}/{urllib.parse.quote(category)}/{urllib.parse.quote(fname)}"
            try:
                download_file(url, dest)
                got += 1
            except Exception:
                pass
        print(f"  {category:<55} {got}/{len(sample)} downloaded (weight={limit})")


def fetch_plantdoc():
    print("\n" + "=" * 55)
    print("Fetching other_plant_leaves_field/ from PlantDoc (GitHub)")
    print("=" * 55)

    tree = http_get_json(PLANTDOC_TREE_API)
    files_by_category = {}
    for item in tree["tree"]:
        if item["type"] != "blob":
            continue
        parts = item["path"].split("/")
        if len(parts) != 3 or parts[0] not in ("train", "test"):
            continue
        split, category, fname = parts
        if category.startswith("Tomato"):
            continue
        files_by_category.setdefault(category, []).append((split, fname))

    print(f"  {len(files_by_category)} non-tomato species/disease categories found "
          f"({sum(len(v) for v in files_by_category.values())} images total)")

    for category, files in sorted(files_by_category.items()):
        safe_name = category.replace(" ", "_").replace(",", "")
        cat_dir = FIELD_LEAVES_DIR / safe_name
        cat_dir.mkdir(parents=True, exist_ok=True)

        already = len(list(cat_dir.glob("*.*")))
        if already >= len(files):
            print(f"  {category:<30} already have {already}, skipping")
            continue

        got = 0
        for split, fname in files:
            # Prefix with split -- train/ and test/ can have same filenames.
            dest = cat_dir / f"{split}_{fname}"
            if dest.exists():
                got += 1
                continue
            url = f"{PLANTDOC_RAW_BASE}/{split}/{urllib.parse.quote(category)}/{urllib.parse.quote(fname)}"
            try:
                download_file(url, dest)
                got += 1
            except Exception:
                pass
        print(f"  {category:<30} {got}/{len(files)} downloaded")


FOOD101_ROWS_API = "https://datasets-server.huggingface.co/rows"
FOOD101_DATASET = "ethz/food101"
FOOD101_BLOCK_SIZE = 750  # confirmed via /size: 75750 train rows / 101 classes, contiguous per class
FOOD101_PER_CLASS = 20    # ~101 classes * 20 = ~2000, matching CIFAR-100's prior scale


def fetch_food101():
    """Replaces the old CIFAR-100 source. CIFAR-100 images are natively
    32x32 -- stretched to the validator's 224x224 input they're extremely
    blurry/blocky, nothing like a real photo a user would upload. That's the
    same class of shortcut-learning risk as the lab-vs-field leaf photos:
    the model could learn "blurry = random_object" instead of "this is a
    mundane object, not a leaf", which wouldn't generalize to a real sharp
    photo (e.g. the cake photo that was the original reported failure).
    Food-101 (ethz/food101 on Hugging Face) gives full-resolution real
    photos across 101 food categories -- fetched via HF's public
    datasets-server API, no auth needed, without downloading the full ~5GB
    archive.
    """
    print("\n" + "=" * 55)
    print("Fetching random_objects/ from Food-101 (replaces CIFAR-100)")
    print("=" * 55)

    old_cifar = list(OBJECTS_DIR.glob("cifar_*.png"))
    if old_cifar:
        print(f"  Removing {len(old_cifar)} old low-res CIFAR-100 images...")
        for f in old_cifar:
            f.unlink()

    first = http_get_json(
        f"{FOOD101_ROWS_API}?dataset={urllib.parse.quote(FOOD101_DATASET, safe='')}"
        f"&config=default&split=train&offset=0&length=1"
    )
    class_names = first["features"][1]["type"]["names"]
    print(f"  {len(class_names)} food categories, {FOOD101_PER_CLASS} images each")

    got_total = 0
    for i in range(len(class_names)):
        offset = i * FOOD101_BLOCK_SIZE
        try:
            data = http_get_json(
                f"{FOOD101_ROWS_API}?dataset={urllib.parse.quote(FOOD101_DATASET, safe='')}"
                f"&config=default&split=train&offset={offset}&length={FOOD101_PER_CLASS}"
            )
        except Exception as e:
            print(f"  block {i:<3} FAILED to list: {e}")
            continue

        rows = data.get("rows", [])
        if not rows:
            continue
        label_name = class_names[rows[0]["row"]["label"]]

        got = 0
        for j, r in enumerate(rows):
            dest = OBJECTS_DIR / f"food101_{label_name}_{j}.jpg"
            if dest.exists():
                got += 1
                continue
            try:
                download_file(r["row"]["image"]["src"], dest)
                got += 1
            except Exception:
                pass
        got_total += got
        print(f"  {label_name:<30} {got}/{len(rows)} downloaded")

    print(f"  Total: {got_total} images")


def main():
    LEAVES_DIR.mkdir(parents=True, exist_ok=True)
    FIELD_LEAVES_DIR.mkdir(parents=True, exist_ok=True)
    OBJECTS_DIR.mkdir(parents=True, exist_ok=True)

    fetch_plantvillage()
    fetch_plantdoc()
    fetch_food101()

    n_leaves = sum(1 for _ in LEAVES_DIR.rglob("*.jpg")) + sum(1 for _ in LEAVES_DIR.rglob("*.JPG"))
    n_field = sum(1 for _ in FIELD_LEAVES_DIR.rglob("*.*"))
    n_objects = sum(1 for _ in OBJECTS_DIR.glob("*.jpg"))
    print("\n" + "=" * 55)
    print("Done")
    print("=" * 55)
    print(f"  other_plant_leaves/       : {n_leaves} images (PlantVillage, lab-style)")
    print(f"  other_plant_leaves_field/ : {n_field} images (PlantDoc, field-condition)")
    print(f"  random_objects/           : {n_objects} images")
    print("\nNext: review the data, then update train_leaf_validator.py's")
    print("OTHER_LEAF_DIRS to include other_plant_leaves_field/ too, and")
    print("retrain when ready.")


if __name__ == "__main__":
    main()
