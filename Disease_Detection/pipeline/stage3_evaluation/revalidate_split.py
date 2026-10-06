"""
Re-run YOLOv8n/s/m evaluation on the VALIDATION split (not test) for proper
model-selection methodology, and also on the test split as a sanity check
against already-reported Table III numbers.
"""
from ultralytics import YOLO

DATA_YAML = r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection\data\splits\data.yaml"

models = {
    "YOLOv8n": r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection\models\yolov8n_compare\weights\best.pt",
    "YOLOv8s": r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection\models\yolov8s_compare\weights\best.pt",
    "YOLOv8m": r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection\models\yolov8m_final\weights\best.pt",
}

def main():
    for name, weights in models.items():
        print("=" * 60)
        print(name, "on VALIDATION split")
        print("=" * 60)
        model = YOLO(weights)
        r = model.val(data=DATA_YAML, split="val", imgsz=640, batch=16, workers=0, plots=False, verbose=False)
        print(f"  P={r.box.mp:.3f}  R={r.box.mr:.3f}  mAP50={r.box.map50:.3f}  mAP50-95={r.box.map:.3f}")
        p, rec = r.box.mp, r.box.mr
        f1 = 2 * p * rec / (p + rec) if (p + rec) else 0.0
        print(f"  F1(from P,R)={f1:.3f}")

        print(f"\n{name} on TEST split (sanity check vs existing Table III)")
        r2 = model.val(data=DATA_YAML, split="test", imgsz=640, batch=16, workers=0, plots=False, verbose=False)
        print(f"  P={r2.box.mp:.3f}  R={r2.box.mr:.3f}  mAP50={r2.box.map50:.3f}  mAP50-95={r2.box.map:.3f}")
        p2, rec2 = r2.box.mp, r2.box.mr
        f12 = 2 * p2 * rec2 / (p2 + rec2) if (p2 + rec2) else 0.0
        print(f"  F1(from P,R)={f12:.3f}")
        print()


if __name__ == "__main__":
    main()
