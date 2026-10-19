"""Image-level co-occurrence evaluation of the deployed YOLOv8s on the test split.
Definition: among test images whose ground-truth labels contain >= 2 distinct classes,
count images where every ground-truth class is also predicted at least once at the
deployed thresholds (conf 0.30, IoU 0.45). Also reports strict (no extra class) rate,
and single-class image recall of the class set for context."""
import json
from pathlib import Path
from collections import Counter
from ultralytics import YOLO

BASE = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
NAMES = ["Early_Blight", "Late_Blight", "Healthy", "Leaf_Miner"]


def main():
    model = YOLO(str(BASE / "models" / "yolov8s_compare" / "weights" / "best.pt"))
    img_dir = BASE / "data" / "splits" / "test" / "images"
    lbl_dir = BASE / "data" / "splits" / "test" / "labels"
    out = {"conf": None}
    for conf in (0.25, 0.30):
        rows = []
        for img in sorted(img_dir.iterdir()):
            lbl = lbl_dir / (img.stem + ".txt")
            gt = {int(l.split()[0]) for l in lbl.read_text().splitlines() if l.strip()}
            r = model.predict(str(img), conf=conf, iou=0.45, imgsz=640, verbose=False, device="cpu")[0]
            pred = {int(c) for c in r.boxes.cls.tolist()} if r.boxes is not None else set()
            rows.append((img.name, gt, pred))
        multi = [(n, g, p) for n, g, p in rows if len(g) >= 2]
        all_found = [x for x in multi if x[1] <= x[2]]
        strict = [x for x in multi if x[1] == x[2]]
        # co-occurrence among disease/pest classes only (exclude Healthy)
        multi_d = [(n, g - {2}, p - {2}) for n, g, p in rows if len(g - {2}) >= 2]
        all_found_d = [x for x in multi_d if x[1] <= x[2]]
        combos = Counter(tuple(sorted(NAMES[i] for i in g)) for _, g, _ in multi)
        res = {
            "conf": conf, "test_images": len(rows),
            "multi_class_images": len(multi), "all_gt_classes_detected": len(all_found),
            "rate_all_detected": round(len(all_found) / max(len(multi), 1), 4),
            "exact_class_set_match": len(strict),
            "multi_disease_images_excl_healthy": len(multi_d),
            "multi_disease_all_detected": len(all_found_d),
            "combos": {" + ".join(k): v for k, v in combos.items()},
        }
        print(json.dumps(res, indent=1))
        out[str(conf)] = res
    (Path(__file__).parent / "cooc_eval_result.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
