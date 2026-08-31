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
import pickle
import random
import shutil
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
OUT_DIR = BASE / "data" / "leaf_validator_negatives"
LEAVES_DIR = OUT_DIR / "other_plant_leaves"
OBJECTS_DIR = OUT_DIR / "random_objects"

GITHUB_API = "https://api.github.com/repos/spMohanty/PlantVillage-Dataset/contents/raw/color"
RAW_BASE = "https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/raw/color"

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


def download_large_file(url, dest_path, max_attempts=8):
    """Resumable chunked download for big files (the CIFAR-100 archive).
    cs.toronto.edu's server has repeatedly dropped the connection partway
    through (first at ~5MB, then ~41MB) -- a longer timeout alone doesn't
    help since these aren't timeouts, the connection just stops delivering
    data. This retries with an HTTP Range request picking up from however
    many bytes are already on disk, instead of restarting from zero."""
    chunk_size = 1024 * 1024

    for attempt in range(1, max_attempts + 1):
        existing = dest_path.stat().st_size if dest_path.exists() else 0
        req = urllib.request.Request(url, headers=dict(REQUEST_HEADERS))
        if existing:
            req.add_header("Range", f"bytes={existing}-")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resuming = resp.status == 206
                if existing and not resuming:
                    # Server ignored the Range request -- start over cleanly
                    # rather than risk a corrupt double-written file.
                    existing = 0
                content_range_total = resp.headers.get("Content-Range", "")
                if "/" in content_range_total:
                    total = int(content_range_total.rsplit("/", 1)[1])
                else:
                    total = existing + int(resp.headers.get("Content-Length", 0))

                mode = "ab" if resuming else "wb"
                written = existing
                with open(dest_path, mode) as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        written += len(chunk)
                        if total:
                            print(f"    {written / 1e6:.0f}MB / {total / 1e6:.0f}MB "
                                  f"(attempt {attempt})", flush=True)

            if total and written < total:
                raise IOError(f"Incomplete: got {written} of {total} bytes")
            return  # success

        except Exception as e:
            print(f"    Attempt {attempt}/{max_attempts} failed at "
                  f"{dest_path.stat().st_size if dest_path.exists() else 0} bytes: {e}", flush=True)
            if attempt == max_attempts:
                dest_path.unlink(missing_ok=True)
                raise
            time.sleep(min(5 * attempt, 30))


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


def fetch_cifar100():
    print("\n" + "=" * 55)
    print("Fetching random_objects/ from CIFAR-100")
    print("=" * 55)

    TARGET_COUNT = 1800
    already = list(OBJECTS_DIR.glob("*.png"))
    if len(already) >= TARGET_COUNT:
        print(f"  Already have {len(already)} images, skipping download.")
        return

    url = "https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz"
    archive_path = OUT_DIR / "cifar-100-python.tar.gz"
    if not archive_path.exists():
        print(f"  Downloading {url} (~169MB)...")
        download_large_file(url, archive_path)
        print("  Downloaded.")

    print("  Extracting...")
    with tarfile.open(archive_path) as tar:
        tar.extractall(OUT_DIR)

    train_pickle = OUT_DIR / "cifar-100-python" / "train"
    with open(train_pickle, "rb") as f:
        batch = pickle.load(f, encoding="bytes")

    data = batch[b"data"]  # (N, 3072) uint8, R/G/B channels flattened
    n = data.shape[0]
    random.seed(42)
    indices = random.sample(range(n), min(TARGET_COUNT, n))

    for i, idx in enumerate(indices):
        img_flat = data[idx]
        img = img_flat.reshape(3, 32, 32).transpose(1, 2, 0)  # -> HWC
        Image.fromarray(img).save(OBJECTS_DIR / f"cifar_{idx}.png")

    print(f"  Saved {len(indices)} images to {OBJECTS_DIR}")

    # Cleanup the archive + extracted pickle folder, keep only the images.
    archive_path.unlink(missing_ok=True)
    shutil.rmtree(OUT_DIR / "cifar-100-python", ignore_errors=True)
    print("  Cleaned up archive/pickle files.")


def main():
    LEAVES_DIR.mkdir(parents=True, exist_ok=True)
    OBJECTS_DIR.mkdir(parents=True, exist_ok=True)

    fetch_plantvillage()
    fetch_cifar100()

    n_leaves = sum(1 for _ in LEAVES_DIR.rglob("*.jpg")) + sum(1 for _ in LEAVES_DIR.rglob("*.JPG"))
    n_objects = sum(1 for _ in OBJECTS_DIR.glob("*.png"))
    print("\n" + "=" * 55)
    print("Done")
    print("=" * 55)
    print(f"  other_plant_leaves/ : {n_leaves} images")
    print(f"  random_objects/     : {n_objects} images")
    print("\nNext: review the data, then update train_leaf_validator.py's")
    print("NOT_TOMATO_DIRS to include these two folders, and retrain when ready.")


if __name__ == "__main__":
    main()
