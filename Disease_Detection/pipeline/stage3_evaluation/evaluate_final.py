# evaluate_final.py
# Evaluates best model on held-out test set
# Run from stage3_evaluation folder:
#   python evaluate_final.py

from ultralytics import YOLO
from pathlib import Path


def main():
    MODEL = r"C:\tomato_yolo_v2\runs\yolov8m_symptom\weights\best.pt"
    DATA  = r"C:\Users\mfart\Desktop\Research\Disease Detection\data\splits\data.yaml"

    print("=" * 55)
    print("Final Evaluation on TEST SET")
    print("Model : YOLOv8m clean dataset (best model)")
    print("=" * 55)

    model = YOLO(MODEL)
    metrics = model.val(
        data    = DATA,
        split   = "test",
        conf    = 0.25,
        iou     = 0.45,
        workers = 0,
        verbose = True,
        plots   = True,
        project = r"C:\Users\mfart\Desktop\Research\Disease Detection\output\metrics",
        name    = "final_evaluation",
    )

    print("\n" + "=" * 55)
    print("TEST SET RESULTS")
    print("=" * 55)
    print(f"  mAP@0.5      : {round(float(metrics.box.map50), 4)}")
    print(f"  mAP@0.5:0.95 : {round(float(metrics.box.map), 4)}")
    print(f"  Precision    : {round(float(metrics.box.mp), 4)}")
    print(f"  Recall       : {round(float(metrics.box.mr), 4)}")
    print()
    for i, name in enumerate(["Early_Blight", "Late_Blight"]):
        print(f"  AP50 {name:<15} : {round(float(metrics.box.ap50[i]), 4)}")
    print("=" * 55)
    print("\nResults saved to output\\metrics\\final_evaluation")


if __name__ == "__main__":
    main()