"""
Automated Weather Dataset Update Pipeline for Sri Lankan Tomato Price Advisor.
Fetches daily rainfall and mean temperature from Open-Meteo API for all 4 key stations
(Anuradhapura, Badulla, Dambulla, Nuwara Eliya) from the dataset cutoff to today,
formats the data, appends non-duplicate records to datasets/historical_weather_sri_lanka.csv,
and verifies the updated Z-score calculation.
"""

from pathlib import Path
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

CSV_PATH = BASE_DIR / "datasets" / "historical_weather_sri_lanka.csv"

# Station Coordinates
STATIONS_CONFIG = {
    "Anuradhapura": {"lat": 8.3114, "lon": 80.4037},
    "Badulla": {"lat": 6.9934, "lon": 81.0550},
    "Dambulla": {"lat": 7.8567, "lon": 80.6517},
    "Nuwara Eliya": {"lat": 6.9497, "lon": 80.7891},
}

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_open_meteo_daily(lat: float, lon: float, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch daily precipitation_sum and temperature_2m_mean from Open-Meteo.
    Tries Archive API first; if archive API ends prior to end_date (due to ERA5 lag),
    supplements missing recent days with Forecast API.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["precipitation_sum", "temperature_2m_mean"],
        "timezone": "Asia/Colombo",
    }

    df_result = pd.DataFrame()

    # 1. Query Archive API
    try:
        resp = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            daily = data.get("daily", {})
            times = daily.get("time", [])
            rain = daily.get("precipitation_sum", [])
            temp = daily.get("temperature_2m_mean", [])
            if times:
                df_result = pd.DataFrame({
                    "Date": times,
                    "Rainfall(mm)": rain,
                    "Temperature(°C)": temp,
                })
    except Exception as exc:
        print(f"    Archive API warning: {exc}")

    # 2. Check if end_date was reached. If missing recent days (ERA5 delay), query Forecast API.
    if df_result.empty or (df_result["Date"].max() < end_date):
        actual_start = start_date
        if not df_result.empty:
            max_archive_date = pd.to_datetime(df_result["Date"].max())
            actual_start = (max_archive_date + timedelta(days=1)).strftime("%Y-%m-%d")

        if actual_start <= end_date:
            try:
                forecast_params = {
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": actual_start,
                    "end_date": end_date,
                    "daily": ["precipitation_sum", "temperature_2m_mean"],
                    "timezone": "Asia/Colombo",
                }
                resp_f = requests.get(OPEN_METEO_FORECAST_URL, params=forecast_params, timeout=10)
                if resp_f.status_code == 200:
                    data_f = resp_f.json()
                    daily_f = data_f.get("daily", {})
                    times_f = daily_f.get("time", [])
                    rain_f = daily_f.get("precipitation_sum", [])
                    temp_f = daily_f.get("temperature_2m_mean", [])
                    if times_f:
                        df_f = pd.DataFrame({
                            "Date": times_f,
                            "Rainfall(mm)": rain_f,
                            "Temperature(°C)": temp_f,
                        })
                        df_result = pd.concat([df_result, df_f], ignore_index=True)
            except Exception as exc:
                print(f"    Forecast API warning: {exc}")

    if not df_result.empty:
        df_result["Rainfall(mm)"] = pd.to_numeric(df_result["Rainfall(mm)"], errors="coerce").fillna(0.0).round(1)
        df_result["Temperature(°C)"] = pd.to_numeric(df_result["Temperature(°C)"], errors="coerce").fillna(25.0).round(1)

    return df_result


def update_weather_dataset():
    print("==================================================================================")
    print(" AUTOMATED WEATHER DATASET UPDATE PIPELINE (OPEN-METEO API)")
    print("==================================================================================\n")

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Weather dataset missing at {CSV_PATH}")

    existing_df = pd.read_csv(CSV_PATH)
    existing_df.columns = [c.strip() for c in existing_df.columns]
    
    # Standardize column name
    existing_df = existing_df.rename(columns={"Temperature(?C)": "Temperature(°C)"})
    
    max_date_str = existing_df["Date"].max()
    print(f"Current CSV Path: {CSV_PATH}")
    print(f"Current Latest Date in CSV: {max_date_str}")
    print(f"Current Dataset Shape: {existing_df.shape}\n")

    max_dt = pd.to_datetime(max_date_str)
    next_dt = max_dt + timedelta(days=1)
    today_dt = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))

    if next_dt > today_dt:
        print("Dataset is already up to date with today! No new days needed.")
        return

    start_date_str = next_dt.strftime("%Y-%m-%d")
    end_date_str = today_dt.strftime("%Y-%m-%d")
    print(f"Fetching missing weather data from {start_date_str} to {end_date_str}...\n")

    new_rows_list = []
    added_summary = {}

    for station, coords in STATIONS_CONFIG.items():
        print(f"Fetching Open-Meteo data for '{station}' (lat={coords['lat']}, lon={coords['lon']})...")
        s_df = fetch_open_meteo_daily(coords["lat"], coords["lon"], start_date_str, end_date_str)
        if s_df.empty:
            print(f"  Warning: No data returned for station {station}")
            added_summary[station] = 0
            continue

        s_df["Location"] = station
        # Match exact CSV column order: Date, Location, Rainfall(mm), Temperature(°C)
        s_df = s_df[["Date", "Location", "Rainfall(mm)", "Temperature(°C)"]]
        new_rows_list.append(s_df)
        added_summary[station] = len(s_df)
        print(f"  -> {len(s_df)} new daily records fetched (Dates: {s_df['Date'].min()} to {s_df['Date'].max()})")

    if not new_rows_list:
        print("\nNo new records were fetched.")
        return

    new_df = pd.concat(new_rows_list, ignore_index=True)

    # Combine existing + new, remove exact duplicates
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df["Date_DT"] = pd.to_datetime(combined_df["Date"])
    combined_df = combined_df.drop_duplicates(subset=["Date", "Location"]).sort_values(["Date_DT", "Location"]).reset_index(drop=True)
    combined_df = combined_df.drop(columns=["Date_DT"])

    # Overwrite CSV with updated dataset
    combined_df.to_csv(CSV_PATH, index=False)
    
    print("\n----------------------------------------------------------------------------------")
    print(" UPDATE SUMMARY")
    print("----------------------------------------------------------------------------------")
    for st, cnt in added_summary.items():
        print(f"  - Station '{st}': +{cnt} rows added")
    print(f"New Total Rows in CSV: {len(combined_df)}")
    print(f"New Latest Date in CSV: {combined_df['Date'].max()}")

    # Run verification check with RegionalWeatherService
    print("\n==================================================================================")
    print(" VERIFICATION: REGIONAL WEATHER Z-SCORE CALCULATION FOR TODAY")
    print("==================================================================================")
    
    # Reload service to compute on updated CSV
    from app.services.regional_weather_service import RegionalWeatherService
    fresh_service = RegionalWeatherService(weather_csv=CSV_PATH)
    
    today_str = end_date_str
    print(f"Target Date requested by API: {today_str}\n")
    
    for station in STATIONS_CONFIG.keys():
        feat = fresh_service.get_station_features(station, today_str)
        print(f"Station: {station}")
        print(f"  - Actual Date of Row Selected from CSV: {feat['date']}")
        print(f"  - 21-Day Cumulative Rainfall: {feat['rain_21d_cum_mm']} mm")
        print(f"  - Monthly Baseline Mean (August mu): {feat['rain_21d_mean_mm']} mm")
        print(f"  - Output Z-Score: {feat['rain_21d_z']} ({'SEVERE' if abs(feat['rain_21d_z'])>=2 else 'MODERATE' if abs(feat['rain_21d_z'])>=1 else 'LOW'})")

if __name__ == "__main__":
    update_weather_dataset()
