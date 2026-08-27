# evaluate_final.py
# Evaluates the final 4-class model on the held-out test set.
# Supersedes the earlier 2-class-only version of this script.
#
# Run from stage3_evaluation folder (after stage2_model_training\train_final.py):
#   python evaluate_final.py

import json
from ultralytics import YOLO
from pathlib import Path

CLASS_NAMES = ["Early_Blight", "Late_Blight", "Healthy", "Leaf_Miner"]


def main():
    BASE = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
    MODEL = BASE / "models" / "yolov8m_final" / "weights" / "best.pt"
    DATA = BASE / "data" / "splits" / "data.yaml"
    OUT_DIR = BASE / "output" / "metrics"

    print("=" * 55)
    print("Final Evaluation on TEST SET")
    print("Model : YOLOv8m 4-class final")
    print("=" * 55)

    model = YOLO(str(MODEL))
    # No explicit conf/iou here -- Ultralytics' validation-mode defaults
    # (conf~0.001, iou~0.6) are what mAP is actually supposed to be computed
    # over. A fixed conf=0.25 cutoff (fine for live inference, wrong for
    # benchmarking) drops true positives before mAP is calculated at all,
    # artificially deflating the score -- confirmed by testing: this changed
    # mAP50-95 from 0.44 to the correct 0.48 reported throughout this project.
    metrics = model.val(
        data    = str(DATA),
        split   = "test",
        imgsz   = 640,
        workers = 0,
        verbose = True,
        plots   = True,
        project = str(OUT_DIR),
        name    = "final_evaluation",
        exist_ok= True,
    )

    f1_overall = 2 * metrics.box.mp * metrics.box.mr / (metrics.box.mp + metrics.box.mr + 1e-9)

    print("\n" + "=" * 55)
    print("TEST SET RESULTS -- OVERALL")
    print("=" * 55)
    print(f"  mAP@0.5      : {round(float(metrics.box.map50), 4)}")
    print(f"  mAP@0.5:0.95 : {round(float(metrics.box.map), 4)}")
    print(f"  Precision    : {round(float(metrics.box.mp), 4)}")
    print(f"  Recall       : {round(float(metrics.box.mr), 4)}")
    print(f"  F1           : {round(float(f1_overall), 4)}")

    print("\n" + "=" * 55)
    print("TEST SET RESULTS -- PER CLASS")
    print("=" * 55)
    per_class = []
    for i, cid in enumerate(metrics.ap_class_index):
        name = CLASS_NAMES[cid]
        p, r = float(metrics.box.p[i]), float(metrics.box.r[i])
        f1 = 2 * p * r / (p + r + 1e-9)
        m50, m5095 = float(metrics.box.ap50[i]), float(metrics.box.ap[i])
        print(f"  {name:<15} P={p:.4f} R={r:.4f} F1={f1:.4f} mAP50={m50:.4f} mAP50-95={m5095:.4f}")
        per_class.append({"class": name, "precision": p, "recall": r, "f1": f1,
                           "mAP50": m50, "mAP50_95": m5095})

    summary = {
        "overall": {
            "precision": float(metrics.box.mp), "recall": float(metrics.box.mr),
            "f1": float(f1_overall), "mAP50": float(metrics.box.map50),
            "mAP50_95": float(metrics.box.map),
        },
        "per_class": per_class,
    }
    summary_path = OUT_DIR / "final_evaluation" / "metrics_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("=" * 55)
    print(f"\nResults saved to {OUT_DIR / 'final_evaluation'}")
    print(f"Summary JSON    : {summary_path}")


if __name__ == "__main__":
    main()
