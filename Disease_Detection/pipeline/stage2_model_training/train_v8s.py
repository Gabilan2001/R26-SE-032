# train_v8s.py
# Trains YOLOv8s on the exact same final 4-class dataset (Early_Blight,
# Late_Blight, Healthy, Leaf_Miner), native 640x640 resolution, from fresh
# COCO-pretrained weights -- identical setup to train_final.py (YOLOv8m),
# only the base model swapped, for a fair size/accuracy comparison across
# YOLOv8m vs YOLOv8s vs YOLOv8n on the paper's model-comparison section.
#
# Save to:
#   <repo>\Disease_Detection\pipeline\stage2_model_training\
#
# Run from same folder (after stage1_data_preparation\merge_final.py):
#   python train_v8s.py

import torch
from pathlib import Path
from ultralytics import YOLO


def main():
    BASE = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032\Disease_Detection")
    DATA = BASE / "data" / "splits" / "data.yaml"
    RUNS = BASE / "models"

    print("=" * 55)
    print("YOLOv8s -- Model Comparison Training")
    print("4-Class: Early_Blight, Late_Blight, Healthy, Leaf_Miner")
    print("=" * 55)
    print(f"\nGPU  : {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"     {torch.cuda.get_device_name(0)}")
        print(f"     {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB VRAM")

    device = "0" if torch.cuda.is_available() else "cpu"

    model = YOLO("yolov8s.pt")  # fresh COCO-pretrained weights

    model.train(
        data         = str(DATA),
        imgsz        = 640,
        epochs       = 100,
        batch        = 16,
        device       = device,
        workers      = 0,
        seed         = 42,
        deterministic= True,
        # same augmentation config as train_final.py -- only the base model
        # differs, so the comparison isolates model-size effects
        mosaic       = 1.0,
        hsv_h        = 0.015,
        hsv_s        = 0.7,
        hsv_v        = 0.4,
        translate    = 0.1,
        scale        = 0.5,
        fliplr       = 0.5,
        flipud       = 0.0,
        close_mosaic = 10,
        amp          = True,
        project      = str(RUNS),
        name         = "yolov8s_compare",
        exist_ok     = True,
        save         = True,
        plots        = True,
        val          = True,
        patience     = 20,
        verbose      = True,
    )

    best = RUNS / "yolov8s_compare" / "weights" / "best.pt"
    print("\n" + "=" * 55)
    print("Training Complete")
    print("=" * 55)
    print(f"  Best weights : {best}")
    print("\nNext: train_v8n.py, then stage3_evaluation\\evaluate_models.py")


if __name__ == "__main__":
    main()
