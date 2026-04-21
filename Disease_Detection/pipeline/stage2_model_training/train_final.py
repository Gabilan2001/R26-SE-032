# train_final.py
# Trains YOLOv8m on final merged dataset
# (studio + field images, symptom-level annotations)
#
# Save to:
#   C:\Users\mfart\Desktop\Research\Disease Detection\pipeline\stage2_model_training\
#
# Run from same folder:
#   python train_final.py

import torch
from pathlib import Path
from ultralytics import YOLO


def main():
    BASE     = Path(r"C:\Users\mfart\Desktop\Research\Disease Detection")
    DATA     = BASE / "data" / "splits" / "data.yaml"
    RUNS     = BASE / "models"

    print("=" * 55)
    print("YOLOv8m — Final Training")
    print("Studio + Field Images — Symptom Level")
    print("=" * 55)
    print(f"\nGPU  : {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"     {torch.cuda.get_device_name(0)}")
        print(f"     {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB VRAM")

    device = "0" if torch.cuda.is_available() else "cpu"

    model = YOLO("yolov8m.pt")

    model.train(
        data         = str(DATA),
        imgsz        = 640,
        epochs       = 100,
        batch        = 16,
        device       = device,
        workers      = 0,
        optimizer    = "AdamW",
        lr0          = 1e-3,
        lrf          = 0.01,
        cos_lr       = True,
        warmup_epochs= 3,
        weight_decay = 5e-4,
        mosaic       = 1.0,
        mixup        = 0.15,
        copy_paste   = 0.3,
        degrees      = 15.0,
        translate    = 0.1,
        scale        = 0.5,
        fliplr       = 0.5,
        flipud       = 0.2,
        hsv_h        = 0.015,
        hsv_s        = 0.7,
        hsv_v        = 0.4,
        erasing      = 0.4,
        box          = 7.5,
        cls          = 1.0,
        dfl          = 1.5,
        amp          = True,
        project      = str(RUNS),
        name         = "yolov8m_final",
        exist_ok     = True,
        save         = True,
        save_period  = 10,
        plots        = True,
        val          = True,
        patience     = 35,
        close_mosaic = 10,
        verbose      = True,
        seed         = 42,
    )

    best = RUNS / "yolov8m_final" / "weights" / "best.pt"
    print("\n" + "=" * 55)
    print("Training Complete")
    print("=" * 55)
    print(f"  Best weights : {best}")
    print("\nNext: run stage3_evaluation\\evaluate_final.py")


if __name__ == "__main__":
    main()
