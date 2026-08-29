"""
READ-ONLY Comprehensive System Architecture Audit Script.
Extracts empirical details from price datasets, weather datasets, ML models, FastAPI routes, services, and frontend code.
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent

def audit_datasets():
    print("==================================================================================")
    print(" 4. PRICE DATA PIPELINE AUDIT")
    print("==================================================================================")

    price_csv = BASE_DIR / "datasets/tomato_prices_vegetablesSriLanka.csv"
    print(f"Price CSV Path: {price_csv}")
    if price_csv.exists():
        df_p = pd.read_csv(price_csv)
        print(f"Total rows: {len(df_p)}")
        print(f"Columns: {list(df_p.columns)}")
        print(f"Unique Items: {df_p['Item'].unique() if 'Item' in df_p.columns else 'N/A'}")
        
        # Filter Tomato
        df_tom = df_p[df_p["Item"].astype(str).str.strip().str.lower() == "tomato"].copy() if "Item" in df_p.columns else df_p.copy()
        print(f"Tomato rows: {len(df_tom)}")
        df_tom['Date'] = pd.to_datetime(df_tom['Date'])
        print(f"Earliest Date: {df_tom['Date'].min().strftime('%Y-%m-%d')}")
        print(f"Latest Date: {df_tom['Date'].max().strftime('%Y-%m-%d')}")
        
        if 'Market' in df_tom.columns and 'Type' in df_tom.columns:
            df_tom['Series'] = df_tom['Market'].astype(str) + "-" + df_tom['Type'].astype(str)
            print("\nRecords per Market Series:")
            for s, grp in df_tom.groupby('Series'):
                print(f"  - {s}: {len(grp)} rows (Earliest: {grp['Date'].min().strftime('%Y-%m-%d')}, Latest: {grp['Date'].max().strftime('%Y-%m-%d')})")

    weather_csv = BASE_DIR / "datasets/historical_weather_sri_lanka.csv"
    print("\n==================================================================================")
    print(" 8. WEATHER DATASET AUDIT")
    print("==================================================================================")
    print(f"Weather CSV Path: {weather_csv}")
    if weather_csv.exists():
        df_w = pd.read_csv(weather_csv)
        print(f"Total rows: {len(df_w)}")
        print(f"Columns: {list(df_w.columns)}")
        df_w['Date'] = pd.to_datetime(df_w['Date'])
        print(f"Earliest Date: {df_w['Date'].min().strftime('%Y-%m-%d')}")
        print(f"Latest Date: {df_w['Date'].max().strftime('%Y-%m-%d')}")
        print(f"Stations: {df_w['Location'].unique() if 'Location' in df_w.columns else 'N/A'}")
        
        print("\nStation Breakdown:")
        for loc, grp in df_w.groupby('Location'):
            print(f"  - {loc}: {len(grp)} rows (Max Date: {grp['Date'].max().strftime('%Y-%m-%d')})")

def audit_models():
    print("\n==================================================================================")
    print(" 5. ML MODEL & SCALER FILE INVENTORY")
    print("==================================================================================")

    models_dir = BASE_DIR / "ml_models"
    print(f"ML Models Directory: {models_dir}")
    if models_dir.exists():
        for f in models_dir.rglob("*"):
            if f.is_file() and f.suffix in [".h5", ".keras", ".pkl", ".joblib", ".json", ".csv"]:
                print(f"  - {f.relative_to(models_dir)} ({f.stat().st_size} bytes)")

def inspect_model_architecture():
    print("\n==================================================================================")
    print(" 5B. BiLSTM ARCHITECTURE DETAILS (TF/KERAS)")
    print("==================================================================================")

    try:
        import tensorflow as tf
        model_path = BASE_DIR / "ml_models/promoted/bilstm_Dambulla_Wholesale.h5"
        if model_path.exists():
            model = tf.keras.models.load_model(model_path, compile=False)
            print("Loaded Model Summary for bilstm_Dambulla_Wholesale.h5:")
            model.summary(print_fn=lambda x: print(f"  {x}"))
            print(f"Input Shape: {model.input_shape}")
            print(f"Output Shape: {model.output_shape}")
    except Exception as e:
        print(f"Model Load Error: {e}")

if __name__ == "__main__":
    audit_datasets()
    audit_models()
    inspect_model_architecture()
