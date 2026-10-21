"""
READ-ONLY Weather-Price Exploratory Feasibility Analysis Script.
Calculates empirical lag correlations (lags 1, 3, 7, 14, 21, 30 days)
between historical weather variables and price series across all 4 markets.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
WEATHER_CSV = BASE_DIR / "datasets" / "historical_weather_sri_lanka.csv"
PRICE_CSV = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"

def audit_weather_dataset():
    print("==================================================================================")
    print(" 4. AUDIT CURRENT WEATHER DATASET")
    print("==================================================================================\n")

    if not WEATHER_CSV.exists():
        print("Weather dataset missing.")
        return

    df_w = pd.read_csv(WEATHER_CSV)
    df_w.columns = [c.strip() for c in df_w.columns]
    print(f"Dataset Path: {WEATHER_CSV}")
    print(f"Total Rows: {len(df_w)}")
    print(f"Columns: {list(df_w.columns)}")
    print(f"Locations Available: {df_w['Location'].unique().tolist()}")

    df_w["Date"] = pd.to_datetime(df_w["Date"])
    print(f"Date Range: {df_w['Date'].min().strftime('%Y-%m-%d')} to {df_w['Date'].max().strftime('%Y-%m-%d')}")
    print(f"Missing Values per Column:\n{df_w.isnull().sum()}\n")

    for loc in df_w['Location'].unique():
        sub = df_w[df_w['Location'] == loc]
        print(f"Location '{loc}': {len(sub)} rows ({sub['Date'].min().strftime('%Y-%m-%d')} to {sub['Date'].max().strftime('%Y-%m-%d')})")
    print("\n")

def run_lag_correlations():
    print("==================================================================================")
    print(" 6. EXPLORATORY WEATHER -> PRICE LAG CORRELATION ANALYSIS")
    print("==================================================================================\n")

    if not WEATHER_CSV.exists() or not PRICE_CSV.exists():
        return

    df_w = pd.read_csv(WEATHER_CSV)
    df_w.columns = [c.strip() for c in df_w.columns]
    df_w["Date"] = pd.to_datetime(df_w["Date"])
    
    # Standardize column names
    df_w = df_w.rename(columns={
        "Rainfall(mm)": "Rainfall_mm",
        "Temperature(°C)": "Temp_C",
        "Temperature(?C)": "Temp_C"
    })
    # Fallback column rename if special char
    for col in df_w.columns:
        if "Rainfall" in col:
            df_w[col] = pd.to_numeric(df_w[col], errors="coerce")
            df_w = df_w.rename(columns={col: "Rainfall_mm"})
        elif "Temp" in col:
            df_w[col] = pd.to_numeric(df_w[col], errors="coerce")
            df_w = df_w.rename(columns={col: "Temp_C"})

    df_p = pd.read_csv(PRICE_CSV)
    df_p.columns = [c.strip() for c in df_p.columns]
    df_tom = df_p[df_p["Item"] == "Tomato"].copy()
    df_tom["Date"] = pd.to_datetime(df_tom["Date"])
    df_tom["Price"] = pd.to_numeric(df_tom["Price"], errors="coerce")

    series_list = [
        ("Dambulla", "Retail"),
        ("Dambulla", "Wholesale"),
        ("Pettah", "Retail"),
        ("Pettah", "Wholesale"),
    ]

    locations = df_w["Location"].unique()
    lags = [1, 3, 7, 14, 21, 30]

    corr_rows = []

    for m, t in series_list:
        sub_p = df_tom[(df_tom["Market"] == m) & (df_tom["Type"] == t)].sort_values("Date").reset_index(drop=True)
        sub_p["Price"] = sub_p["Price"].interpolate(method="linear", limit_direction="both")

        for loc in locations:
            sub_w = df_w[df_w["Location"] == loc].sort_values("Date").reset_index(drop=True)
            
            merged = pd.merge(sub_p[["Date", "Price"]], sub_w, on="Date", how="inner")
            if merged.empty:
                continue

            for var in ["Rainfall_mm", "Temp_C"]:
                if var not in merged.columns:
                    continue
                
                for l in lags:
                    col_name = f"{var}_lag_{l}"
                    merged[col_name] = merged[var].shift(l)
                    valid = merged.dropna(subset=["Price", col_name])
                    if len(valid) > 50:
                        r = valid["Price"].corr(valid[col_name])
                        corr_rows.append({
                            "Series": f"{m}-{t}",
                            "Location": loc,
                            "Variable": var,
                            "Lag": f"{l}d",
                            "Pearson_r": round(r, 4),
                            "N": len(valid)
                        })

    df_corr = pd.DataFrame(corr_rows)
    if not df_corr.empty:
        print("Top Positive Correlations:")
        print(df_corr.sort_values("Pearson_r", ascending=False).head(10).to_string(index=False))
        print("\nTop Negative Correlations:")
        print(df_corr.sort_values("Pearson_r", ascending=True).head(10).to_string(index=False))
        
        print("\nSummary by Lag Period (Average Absolute Pearson r):")
        df_corr["Abs_r"] = df_corr["Pearson_r"].abs()
        lag_summary = df_corr.groupby("Lag")["Abs_r"].mean().reset_index().sort_values("Abs_r", ascending=False)
        print(lag_summary.to_string(index=False))
    print("\n")

if __name__ == "__main__":
    audit_weather_dataset()
    run_lag_correlations()
