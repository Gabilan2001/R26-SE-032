# 🦠 Plant Disease Detection System

A deep learning pipeline for automated plant disease detection using YOLOv8 object detection models. This system supports end-to-end workflows — from raw image ingestion and annotation through model training, evaluation, and real-time inference via a web interface.

---

## 🧪 Project Overview

| Property | Details |
|---|---|
| **Task** | Object Detection — Plant Disease Localization |
| **Models** | YOLOv8s, YOLOv8m |
| **Framework** | Ultralytics YOLOv8 |
| **Backend** | Python |
| **Frontend** | HTML/CSS/JS Dashboard |

---

## 📁 Project Structure

```
Disease Detection/
├── data/
│   ├── annotated/        # Labeled images (YOLO format)
│   ├── augmented/        # Augmented training data
│   ├── raw/              # Original collected images
│   └── splits/           # Train / Val / Test splits
│
├── frontend/
│   └── index.html        # Web-based detection dashboard
│
├── models/
│   ├── yolov8s/          # YOLOv8 Small checkpoints
│   ├── yolov8m/          # YOLOv8 Medium checkpoints
│   └── yolov8m_final/    # Final production model
│
├── output/
│   ├── metrics/          # Training & evaluation metrics
│   ├── predictions/      # Inference results
│   ├── reports/          # Summary reports
│   └── visualizations/   # Plots, confusion matrices, PR curves
│
└── pipeline/
    ├── stage1_data_preparation/
    │   └── merge_final.py       # Data merge & preparation
    ├── stage2_model_training/
    │   └── train_final.py       # YOLOv8 training script
    ├── stage3_evaluation/
    │   └── evaluate_final.py    # Model evaluation
    └── stage4_inference/
        └── app.py               # Inference application
```

---

## 🚀 Pipeline Stages

### Stage 1 — Data Preparation
Merges and preprocesses annotated datasets, validates YOLO labels, and creates stratified train/val/test splits.

```bash
python pipeline/stage1_data_preparation/merge_final.py
```

### Stage 2 — Model Training
Trains YOLOv8 models on the prepared dataset with configurable hyperparameters.

```bash
python pipeline/stage2_model_training/train_final.py
```

### Stage 3 — Evaluation
Evaluates trained models on the test split, generating mAP, precision, recall, and confusion matrices.

```bash
python pipeline/stage3_evaluation/evaluate_final.py
```

### Stage 4 — Inference
Runs the trained model for real-time disease detection via a web application.

```bash
python pipeline/stage4_inference/app.py
```

---

## 🌐 Frontend Dashboard

Open `frontend/index.html` in a browser (with the inference server running) to use the interactive disease detection dashboard.

---

## 🛠 Requirements

- Python 3.8+
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- OpenCV
- NumPy, Pandas, Matplotlib

Install dependencies:
```bash
pip install ultralytics opencv-python numpy pandas matplotlib
```

---

## 📊 Results

Model evaluation results, training curves, and prediction visualizations are stored in the `output/` directory after running the pipeline.

---

## 👤 Author

**Mohamed Farthas**  
Plant Disease Detection Research Project — 2025
