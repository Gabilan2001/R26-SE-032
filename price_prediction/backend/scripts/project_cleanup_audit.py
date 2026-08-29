"""
READ-ONLY Project Cleanup Audit Script.
Gathers empirical metadata on all models, datasets, python source code files,
imports, and recommendation rules without modifying any file.
"""

from pathlib import Path
import os
import glob
import pickle
import json
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

def audit_models():
    print("==================================================================================")
    print(" 1. INVENTORY ALL MODEL FILES")
    print("==================================================================================\n")

    extensions = ["*.h5", "*.keras", "*.pkl", "*.joblib", "*.pt", "*.pth", "*.onnx"]
    model_files = []
    for ext in extensions:
        model_files.extend(list(BASE_DIR.glob(f"**/{ext}")))

    rows = []
    for p in sorted(model_files):
        rel_path = str(p.relative_to(BASE_DIR)).replace("\\", "/")
        st = os.stat(p)
        size_kb = st.st_size / 1024.0
        mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        
        # Check architecture if h5
        arch_info = "N/A"
        if p.suffix == ".h5":
            try:
                m = load_model(p, compile=False)
                arch_info = f"Input: {m.input_shape}, Output: {m.output_shape}, Params: {m.count_params()}"
            except Exception as e:
                arch_info = f"Error loading: {e}"
        elif p.suffix == ".pkl":
            try:
                with open(p, "rb") as f:
                    obj = pickle.load(f)
                arch_info = f"Type: {type(obj).__name__}"
                if hasattr(obj, "data_min_"):
                    arch_info += f", min={obj.data_min_[0]:.1f}, max={obj.data_max_[0]:.1f}"
            except Exception as e:
                arch_info = f"Pickle load error: {e}"

        rows.append({
            "Path": rel_path,
            "Size (KB)": f"{size_kb:.1f}",
            "Last Modified": mtime,
            "Info": arch_info
        })

    df_models = pd.DataFrame(rows)
    print(df_models.to_string(index=False))
    print("\n")

def audit_datasets():
    print("==================================================================================")
    print(" 3. INVENTORY ALL DATASETS")
    print("==================================================================================\n")

    extensions = ["*.csv", "*.xlsx", "*.json", "*.parquet"]
    dataset_files = []
    for ext in extensions:
        dataset_files.extend(list(BASE_DIR.glob(f"**/{ext}")))

    rows = []
    for p in sorted(dataset_files):
        # Ignore git/node_modules/venv
        if any(part.startswith(".") for part in p.parts):
            continue
        rel_path = str(p.relative_to(BASE_DIR)).replace("\\", "/")
        st = os.stat(p)
        size_kb = st.st_size / 1024.0
        mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        row_count = "N/A"
        cols = "N/A"
        date_range = "N/A"
        has_tomato = "N/A"

        if p.suffix == ".csv":
            try:
                df = pd.read_csv(p, low_memory=False)
                row_count = len(df)
                cols = ", ".join(list(df.columns[:5])) + ("..." if len(df.columns) > 5 else "")
                
                # Check for Tomato
                if "Item" in df.columns:
                    has_tomato = "Tomato" in df["Item"].values
                elif "item" in df.columns:
                    has_tomato = "Tomato" in df["item"].values
                elif "crop" in df.columns:
                    has_tomato = "Tomato" in df["crop"].values
                
                # Check for Date
                date_col = None
                for c in ["Date", "date", "year", "Year"]:
                    if c in df.columns:
                        date_col = c
                        break
                if date_col:
                    try:
                        d_series = pd.to_datetime(df[date_col], errors="coerce").dropna()
                        if not d_series.empty:
                            date_range = f"{d_series.min().strftime('%Y-%m-%d')} to {d_series.max().strftime('%Y-%m-%d')}"
                    except Exception:
                        pass
            except Exception as e:
                cols = f"Error: {e}"

        rows.append({
            "Path": rel_path,
            "Rows": row_count,
            "Size (KB)": f"{size_kb:.1f}",
            "Date Range": date_range,
            "Has Tomato": has_tomato,
            "Last Modified": mtime
        })

    df_data = pd.DataFrame(rows)
    print(df_data.to_string(index=False))
    print("\n")

if __name__ == "__main__":
    audit_models()
    audit_datasets()
