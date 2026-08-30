# evaluate_models.py
# Compares YOLOv8m (final), YOLOv8s, YOLOv8n on the held-out TEST set --
# same test split, same evaluation methodology for all three (no conf/iou
# override -- Ultralytics' validation-mode defaults are what mAP is actually
# meant to be computed over; see evaluate_final.py for why). This is the
# fair, apples-to-apples comparison for the paper's model-size-vs-accuracy
# section -- per-epoch validation numbers printed during training are NOT
# this and shouldn't be quoted as final results.
#
# Run from stage3_evaluation folder, after training all 3:
#   stage2_model_training\train_final.py  (YOLOv8m -- already done, this is
#                                           the deployed/final model)
#   stage2_model_training\train_v8s.py
#   stage2_model_training\train_v8n.py
# then:
#   python evaluate_models.py

import json
from pathlib import Path
from ultralytics import YOLO

CLASS_NAMES = ["Early_Blight", "Late_Blight", "Healthy", "Leaf_Miner"]

# label -> training run folder name (under models/)
MODELS = {
    "YOLOv8m": "yolov8m_final",
    "YOLOv8s": "yolov8s_compare",
    "YOLOv8n": "yolov8n_compare",
}


def evaluate_one(label, run_name, base, data, out_dir):
    weights = base / "models" / run_name / "weights" / "best.pt"
    print("\n" + "=" * 55)
    print(f"{label}  ({run_name})")
    print("=" * 55)

    model = YOLO(str(weights))
    n_params = sum(p.numel() for p in model.model.parameters())
    size_mb = weights.stat().st_size / 1e6

    # Same correct methodology as evaluate_final.py -- no conf/iou override.
    metrics = model.val(
        data    = str(data),
        split   = "test",
        imgsz   = 640,
        workers = 0,
        verbose = False,
        plots   = True,
        project = str(out_dir),
        name    = f"{run_name}_evaluation",
        exist_ok= True,
    )

    f1_overall = 2 * metrics.box.mp * metrics.box.mr / (metrics.box.mp + metrics.box.mr + 1e-9)

    per_class = []
    for i, cid in enumerate(metrics.ap_class_index):
        name = CLASS_NAMES[cid]
        p, r = float(metrics.box.p[i]), float(metrics.box.r[i])
        f1 = 2 * p * r / (p + r + 1e-9)
        per_class.append({
            "class": name, "precision": p, "recall": r, "f1": f1,
            "mAP50": float(metrics.box.ap50[i]), "mAP50_95": float(metrics.box.ap[i]),
        })

    # metrics.speed = {"preprocess": ms, "inference": ms, "loss": ms, "postprocess": ms},
    # per image, averaged over the test set -- same numbers Ultralytics prints
    # as "Speed: ...ms preprocess, ...ms inference, ..." at the end of a val run.
    inference_ms = metrics.speed.get("inference", 0.0)
    total_ms = sum(metrics.speed.values())

    result = {
        "label": label,
        "run_name": run_name,
        "params_millions": round(n_params / 1e6, 2),
        "weights_mb": round(size_mb, 2),
        "inference_ms": round(inference_ms, 3),
        "total_pipeline_ms": round(total_ms, 3),
        "fps": round(1000 / total_ms, 1) if total_ms > 0 else None,
        "overall": {
            "precision": float(metrics.box.mp), "recall": float(metrics.box.mr),
            "f1": float(f1_overall), "mAP50": float(metrics.box.map50),
            "mAP50_95": float(metrics.box.map),
        },
        "per_class": per_class,
    }

    print(f"  Params       : {result['params_millions']}M")
    print(f"  Weights size : {result['weights_mb']} MB")
    print(f"  Inference    : {result['inference_ms']} ms/image  (~{result['fps']} FPS full pipeline)")
    print(f"  Precision    : {result['overall']['precision']:.4f}")
    print(f"  Recall       : {result['overall']['recall']:.4f}")
    print(f"  F1           : {result['overall']['f1']:.4f}")
    print(f"  mAP@0.5      : {result['overall']['mAP50']:.4f}")
    print(f"  mAP@0.5:0.95 : {result['overall']['mAP50_95']:.4f}")

    return result


def print_comparison_table(results):
    print("\n" + "=" * 92)
    print("MODEL COMPARISON -- HELD-OUT TEST SET (identical methodology for all 3)")
    print("=" * 92)
    print(f"{'Model':<10}{'Params':>9}{'Size':>10}{'Infer':>11}{'P':>8}{'R':>8}{'F1':>8}{'mAP50':>9}{'mAP50-95':>11}")
    for r in results:
        o = r["overall"]
        print(
            f"{r['label']:<10}{r['params_millions']:>7.2f}M{r['weights_mb']:>8.1f}MB"
            f"{r['inference_ms']:>9.2f}ms{o['precision']:>8.3f}{o['recall']:>8.3f}"
            f"{o['f1']:>8.3f}{o['mAP50']:>9.3f}{o['mAP50_95']:>11.3f}"
        )
    print("=" * 92)

    print("\nPer-class mAP@0.5:0.95:")
    print(f"{'Model':<10}" + "".join(f"{c:<14}" for c in CLASS_NAMES))
    for r in results:
        by_class = {pc["class"]: pc["mAP50_95"] for pc in r["per_class"]}
        row = f"{r['label']:<10}"
        for c in CLASS_NAMES:
            v = by_class.get(c)
            row += f"{v:<14.3f}" if v is not None else f"{'-':<14}"
        print(row)


def main():
    BASE = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
    DATA = BASE / "data" / "splits" / "data.yaml"
    OUT_DIR = BASE / "output" / "metrics"

    print("=" * 55)
    print("Model Comparison -- YOLOv8m vs YOLOv8s vs YOLOv8n")
    print("4-Class: Early_Blight, Late_Blight, Healthy, Leaf_Miner")
    print("Held-out TEST set, identical methodology for all 3")
    print("=" * 55)

    results = []
    for label, run_name in MODELS.items():
        weights = BASE / "models" / run_name / "weights" / "best.pt"
        if not weights.exists():
            print(f"\n[skip] {label}: {weights} not found -- train it first.")
            continue
        results.append(evaluate_one(label, run_name, BASE, DATA, OUT_DIR))

    if not results:
        print("\nNo trained models found to evaluate.")
        return

    print_comparison_table(results)

    summary_path = OUT_DIR / "model_comparison.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull comparison JSON saved to: {summary_path}")


if __name__ == "__main__":
    main()
