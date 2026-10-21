"""
READ-ONLY Diagnostic Script: Weather Z-Score Calculation Audit.
Inspects datasets/historical_weather_sri_lanka.csv and regional_weather_service.py
for exact dates, raw values, baselines, std devs, and output Z-scores on 2026-08-29.
"""

from pathlib import Path
import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.regional_weather_service import RegionalWeatherService, STATIONS

def diagnose_weather():
    print("==================================================================================")
    print(" QUESTION 2: CSV LATEST DATE & SHAPE CHECK")
    print("==================================================================================")
    csv_path = BASE_DIR / "datasets/historical_weather_sri_lanka.csv"
    df = pd.read_csv(csv_path)
    print(f"File Path: {csv_path}")
    print(f"Max Date in CSV: {df['Date'].max()}")
    print(f"Dataset Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

    print("\n==================================================================================")
    print(" QUESTION 1 & 4: DATA SOURCE & DATE FETCHED FOR TARGET DATE = 2026-08-29")
    print("==================================================================================")
    service = RegionalWeatherService()
    target_date = "2026-08-29"
    
    print(f"Target Date requested by API: {target_date}")
    for station in STATIONS:
        feat = service.get_station_features(station, target_date)
        print(f"\nStation: {station}")
        print(f"  - Actual Date of Row Selected from CSV: {feat['date']}")
        print(f"  - Daily Rainfall: {feat['rainfall_daily_mm']} mm")
        print(f"  - 21-Day Cumulative Rainfall (Numerator Input): {feat['rain_21d_cum_mm']} mm")
        print(f"  - Monthly Baseline Mean (mu): {feat['rain_21d_mean_mm']} mm")
        print(f"  - Output Z-Score: {feat['rain_21d_z']}")

    print("\n==================================================================================")
    print(" QUESTION 3: EXACT FORMULA INPUTS & OUTPUTS FOR AUGUST 29, 2026")
    print("==================================================================================")
    
    # Detailed breakdown of baseline stats per station for August vs March
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.month
    
    for station in STATIONS:
        sub = service.df[(service.df["Location"] == station) & (service.df["Date"] <= pd.to_datetime(target_date))].sort_values("Date")
        row = sub.iloc[-1]
        
        actual_date = row["Date"].strftime("%Y-%m-%d")
        month = row["Month"]
        rain_21d = float(row["rain_21d"])
        mean_21d = float(row["rain_21d_mean"])
        std_21d = float(row["rain_21d_std"])
        eps = 1e-5
        z_score = (rain_21d - mean_21d) / (std_21d + eps)
        
        print(f"Station: {station}")
        print(f"  - Date Used: {actual_date} (Month = {month})")
        print(f"  - 21-Day Cumulative Rain (x): {rain_21d:.2f} mm")
        print(f"  - Baseline Monthly Mean (mu): {mean_21d:.2f} mm")
        print(f"  - Baseline Monthly Std (sigma): {std_21d:.2f} mm")
        print(f"  - Formula: ({rain_21d:.2f} - {mean_21d:.2f}) / ({std_21d:.2f} + 1e-5)")
        print(f"  - Calculated Z-score: {z_score:.4f}")
        print(f"  - Service Output Z-score: {row['rain_21d_z']:.4f}\n")

if __name__ == "__main__":
    diagnose_weather()
