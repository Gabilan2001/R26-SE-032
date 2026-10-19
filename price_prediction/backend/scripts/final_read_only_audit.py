"""
READ-ONLY Technical Audit Script for Tomato Price Advisor / Agro Intelligence Pipeline.
Performs empirical verifications across dataset records, code execution paths, LSTM input tensors,
production scalers, model artifacts, live API/service endpoints, recommendations, and SHAP.
"""

from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
import requests
import sys
import os
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.decision_engine_service import (
    get_recent_price_window,
    run_decision_engine,
    get_full_recommendation,
)
from app.services.shap_explainer_service import get_shap_explanation

DATA_PATH = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
MODEL_DIR = BASE_DIR / "ml_models"

SERIES_LIST = [
    ("Dambulla", "Retail"),
    ("Dambulla", "Wholesale"),
    ("Pettah", "Retail"),
    ("Pettah", "Wholesale"),
]

def audit_section_1():
    print("==================================================================================")
    print(" SECTION 1: VERIFY DATASET LATEST RECORDS")
    print("==================================================================================\n")

    df = pd.read_csv(DATA_PATH)
    df.columns = [c.strip() for c in df.columns]
    df_tom = df[df["Item"] == "Tomato"].copy()
    df_tom["Date"] = pd.to_datetime(df_tom["Date"])

    summary_rows = []

    for m, t in SERIES_LIST:
        sub = df_tom[(df_tom["Market"] == m) & (df_tom["Type"] == t)].sort_values("Date").reset_index(drop=True)
        sub["Price"] = pd.to_numeric(sub["Price"], errors="coerce")
        sub["Price_Interp"] = sub["Price"].interpolate(method="linear", limit_direction="both")

        latest_date = sub["Date"].iloc[-1].strftime("%Y-%m-%d")
        latest_price = sub["Price_Interp"].iloc[-1]
        rec_count = len(sub)
        has_target_date = "2026-08-28" in sub["Date"].dt.strftime("%Y-%m-%d").values

        summary_rows.append({
            "Series": f"{m}-{t}",
            "Latest Date": latest_date,
            "Latest Price (LKR)": f"{latest_price:.2f}",
            "Records": rec_count,
            "Has 2026-08-28": has_target_date
        })

    sum_df = pd.DataFrame(summary_rows)
    print(sum_df.to_string(index=False))
    print("\n--- LAST 10 OBSERVATIONS PER SERIES ---\n")

    for m, t in SERIES_LIST:
        sub = df_tom[(df_tom["Market"] == m) & (df_tom["Type"] == t)].sort_values("Date").reset_index(drop=True)
        sub["Price"] = pd.to_numeric(sub["Price"], errors="coerce").interpolate(method="linear", limit_direction="both")
        last_10 = sub.tail(10)
        print(f"Series: {m} {t}")
        print(f"{'Date':<12} | {'Price (LKR)':<12}")
        print("-" * 27)
        for _, row in last_10.iterrows():
            print(f"{row['Date'].strftime('%Y-%m-%d'):<12} | {row['Price']:<12.2f}")
        print()


def audit_section_3_and_4():
    print("==================================================================================")
    print(" SECTION 3 & 4: VERIFY ACTUAL LSTM INPUT WINDOW AND SCALING")
    print("==================================================================================\n")

    for m, t in SERIES_LIST:
        series_label = f"{m}-{t}"
        print(f"--- Series: {series_label} ---")
        
        # 1. Fetch live recent price window
        today_str = datetime.now().strftime("%Y-%m-%d")
        prices, last_date, max_date, cov = get_recent_price_window(m, t, today_str, window_size=10)
        
        # Load sub-df to match dates
        df = pd.read_csv(DATA_PATH)
        df.columns = [c.strip() for c in df.columns]
        sub = df[(df["Market"] == m) & (df["Type"] == t)].sort_values("Date").reset_index(drop=True)
        sub["Date"] = pd.to_datetime(sub["Date"])
        sub_filtered = sub[sub["Date"] <= pd.to_datetime(today_str)].tail(10)
        
        print("Raw 10 Observations Supplied to LSTM:")
        print(f"{'Date':<12} | {'Raw Price (LKR)':<15}")
        print("-" * 30)
        for d, p in zip(sub_filtered["Date"], prices):
            print(f"{d.strftime('%Y-%m-%d'):<12} | {p:<15.2f}")
            
        tensor_shape = (1, len(prices), 1)
        print(f"\nInput Tensor Shape: {tensor_shape}")

        # Section 4: Scaler Audit
        file_suffix = f"{m.lower()}_{t.lower()}"
        scaler_path = MODEL_DIR / f"scaler_{file_suffix}.pkl"
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)

        print(f"Scaler File: {scaler_path.name}")
        print(f"Scaler data_min_: {scaler.data_min_[0]:.2f}")
        print(f"Scaler data_max_: {scaler.data_max_[0]:.2f}")
        
        scaled_vals = scaler.transform(prices.reshape(-1, 1)).flatten()
        print("Transformed Scaled Values (Range [0, 1]):")
        for d, p, s in zip(sub_filtered["Date"], prices, scaled_vals):
            print(f"  {d.strftime('%Y-%m-%d')}: {p:6.2f} LKR -> Scaled: {s:.6f}")
        print("\n")


def audit_section_5():
    print("==================================================================================")
    print(" SECTION 5: VERIFY PRODUCTION MODEL FILES")
    print("==================================================================================\n")

    for m, t in SERIES_LIST:
        file_suffix = f"{m.lower()}_{t.lower()}"
        file_name = f"lstm_{file_suffix}.h5"
        file_path = MODEL_DIR / file_name

        print(f"--- Model File: {file_name} ---")
        print(f"Path: {file_path}")
        print(f"Exists: {file_path.exists()}")
        if file_path.exists():
            st = os.stat(file_path)
            size_kb = st.st_size / 1024.0
            mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"File Size: {size_kb:.2f} KB ({st.st_size} bytes)")
            print(f"Last Modified: {mtime}")

            model = load_model(file_path, compile=False)
            in_shape = model.input_shape
            out_shape = model.output_shape
            print(f"Model Input Shape: {in_shape}")
            print(f"Model Output Shape: {out_shape}")
            print(f"Total Parameters: {model.count_params()}")
            print(f"Layers Count: {len(model.layers)}")
            for idx, lyr in enumerate(model.layers):
                out_s = getattr(lyr, 'output_shape', 'N/A')
                print(f"  Layer {idx+1}: {lyr.name} ({lyr.__class__.__name__}) -> output shape {out_s}")
        print("\n")


def audit_section_6_7_8_9():
    print("==================================================================================")
    print(" SECTION 6, 7, 8, 9: CURRENT FORECAST, API, RECOMMENDATION, AND SHAP VERIFICATION")
    print("==================================================================================\n")

    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"Today's System Request Date: {today_str}\n")

    # Section 6 & 8 Table
    forecast_table = []

    for m, t in SERIES_LIST:
        # Direct Service Call
        rec = get_full_recommendation(market=m, series_type=t, target_date_str=today_str, horizon_days=14)
        
        pt_date = rec["data_as_of_date"]
        pt_price = rec["current_price_lkr"]
        d1 = rec["weather_adjusted_forecast"][0]
        d3 = rec["weather_adjusted_forecast"][2]
        d7 = rec["weather_adjusted_forecast"][6]
        d14 = rec["weather_adjusted_forecast"][13]
        recommendation = rec["recommendation"]
        expected_change = d14 - pt_price

        forecast_table.append({
            "Series": f"{m}-{t}",
            "P(t) Date": pt_date,
            "P(t) (LKR)": f"{pt_price:.2f}",
            "Day 1": f"{d1:.2f}",
            "Day 3": f"{d3:.2f}",
            "Day 7": f"{d7:.2f}",
            "Day 14": f"{d14:.2f}",
            "14-Day Change": f"{expected_change:+.2f}",
            "Recommendation": recommendation
        })

    f_df = pd.DataFrame(forecast_table)
    print("--- PRODUCTION DIRECT FORECAST & RECOMMENDATION TABLE ---")
    print(f_df.to_string(index=False))
    print("\n")

    # Section 7: API Endpoint Comparison
    print("--- SECTION 7: API ENDPOINT VERIFICATION ---")
    api_url = "http://127.0.0.1:8000/predict/"
    try:
        req_payload = {
            "market": "Pettah",
            "type": "Wholesale",
            "forecast_horizon_days": 14
        }
        resp = requests.post(api_url, json=req_payload, timeout=5)
        if resp.status_code == 200:
            api_json = resp.json()
            print(f"API Request Payload: {req_payload}")
            print("API Endpoint Call Successful (HTTP 200)")
            print(f"API Returned Series: {api_json.get('series')}")
            print(f"API Returned Data As Of Date: {api_json.get('data_as_of_date')}")
            print(f"API Returned Current Price P(t): {api_json.get('current_price_lkr'):.2f} LKR/kg")
            print(f"API Returned Day 1 Forecast: {api_json.get('day1_forecast_lkr'):.2f} LKR/kg")
            print(f"API Returned Day 14 Forecast: {api_json.get('day14_forecast_lkr'):.2f} LKR/kg")
            print(f"API Returned Recommendation: {api_json.get('recommendation')}")
        else:
            print(f"API returned HTTP status code: {resp.status_code}")
    except Exception as e:
        print(f"API connection check note: {e}")
    print("\n")

    # Section 9: SHAP Verification
    print("--- SECTION 9: SHAP EXPLAINER VERIFICATION ---")
    for m, t in SERIES_LIST:
        print(f"Testing SHAP for {m}-{t}...")
        shap_res = get_shap_explanation(market=m, series_type=t, target_date_str=today_str)
        if shap_res:
            top_c = shap_res["top_contributor"]
            ranked = shap_res["ranked_timesteps"]
            print(f" -> Execution Successful! Computation time: {shap_res['computation_time_seconds']} sec")
            print(f" -> Total SHAP Timesteps Evaluated: {len(ranked)}")
            print(f" -> Top Contributor: {top_c['timestep_label']} ({top_c['observed_price_lkr']} LKR) -> SHAP: {top_c['shap_contribution_lkr']:+.2f} LKR")
            print(f" -> Summary Sentence: {shap_res['summary_sentence']}\n")
        else:
            print(f" -> SHAP failed for {m}-{t}\n")

if __name__ == "__main__":
    audit_section_1()
    audit_section_3_and_4()
    audit_section_5()
    audit_section_6_7_8_9()
