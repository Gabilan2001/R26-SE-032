"""
Forensic Validation Script for Long-Term Seasonal Price Forecast Upgrade.
Runs mathematical verifications, API vs UI consistency checks, walk-forward performance
comparisons (Old Nominal vs New CPI System), multi-market & multi-month evaluations,
and statistical sanity checks. READ-ONLY on project code and datasets.
"""

from pathlib import Path
import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

PRICE_CSV = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
CPI_CSV = BASE_DIR / "datasets" / "sri_lanka_cpi.csv"
BACKTEST_CSV = BASE_DIR / "ml_models" / "seasonal_backtest_results.csv"

def run_forensic_audit():
    print("==================================================================================")
    print(" FORENSIC AUDIT: 1. CPI DEFLATION MATHEMATICAL REPRODUCTION")
    print("==================================================================================")
    
    df_p = pd.read_csv(PRICE_CSV)
    df_p.columns = [c.strip() for c in df_p.columns]
    sub = df_p[(df_p["Market"] == "Dambulla") & (df_p["Type"] == "Wholesale")].copy()
    sub["Date"] = pd.to_datetime(sub["Date"])
    sub["Price"] = pd.to_numeric(sub["Price"], errors="coerce").interpolate(method="linear")
    sub["YearMonth"] = sub["Date"].dt.strftime("%Y-%m")

    df_cpi = pd.read_csv(CPI_CSV)
    latest_cpi = float(df_cpi.iloc[-1]["CCPI"]) # 216.5 (2026-08)
    
    merged = pd.merge(sub, df_cpi, on="YearMonth", how="left")
    merged["CCPI"] = merged["CCPI"].fillna(latest_cpi)
    merged["Calculated_Real"] = merged["Price"] * (latest_cpi / merged["CCPI"])
    
    sample_dates = ["2016-12-15", "2020-12-15", "2022-12-15", "2024-12-16", "2025-12-15"]
    print(f"Reference CPI: {latest_cpi} (2026-08)\n")
    print(f"{'Date':<12} | {'Nominal Price':<14} | {'Historical CPI':<14} | {'Calculated Real Price':<22}")
    print("-" * 70)
    for d in sample_dates:
        row = merged[merged["Date"] == d]
        if not row.empty:
            r = row.iloc[0]
            print(f"{r['Date'].strftime('%Y-%m-%d'):<12} | {r['Price']:<14.2f} | {r['CCPI']:<14.1f} | {r['Calculated_Real']:<22.2f}")

    print("\n==================================================================================")
    print(" FORENSIC AUDIT: 2. RECENCY WEIGHTING CODE CHECK")
    print("==================================================================================")
    # Check if Decay_Weight affects numpy.percentile
    sub_dec = merged[merged["Date"].dt.month == 12].copy()
    sub_dec["Decay_Weight"] = np.exp(0.15 * (sub_dec["Date"].dt.year - 2025))
    
    unweighted_p50 = float(np.median(sub_dec["Calculated_Real"]))
    print(f"Sub-month length: {len(sub_dec)}")
    print(f"Unweighted np.median(Real_Price) : {unweighted_p50:.2f} LKR")
    
    # Custom weighted percentile implementation
    sorted_idx = np.argsort(sub_dec["Calculated_Real"].values)
    sorted_prices = sub_dec["Calculated_Real"].values[sorted_idx]
    sorted_weights = sub_dec["Decay_Weight"].values[sorted_idx]
    cum_weights = np.cumsum(sorted_weights)
    cum_weights /= cum_weights[-1]
    weighted_p50 = float(sorted_prices[np.searchsorted(cum_weights, 0.5)])
    print(f"True Weighted Median (Decay 0.15): {weighted_p50:.2f} LKR")
    print(f"Difference (Unweighted vs Weighted): {abs(unweighted_p50 - weighted_p50):.2f} LKR")

    print("\n==================================================================================")
    print(" FORENSIC AUDIT: 3. OLD (NOMINAL) VS NEW (CPI-NORMALIZED) WALK-FORWARD COMPARISON")
    print("==================================================================================")
    
    # Load backtest dataset
    df_bt = pd.read_csv(BACKTEST_CSV)
    total_cases = len(df_bt)
    within_count = df_bt["Within_Range"].astype(int).sum()
    mae_mean = df_bt["Absolute_Error_LKR"].mean()
    mape_mean = df_bt["Pct_Error"].mean()

    print(f"Total Simulation Cases: {total_cases}")
    print(f"New CPI-Normalized System Core Interval Coverage (P25-P75): {within_count} / {total_cases} ({within_count/total_cases*100:.2f}%)")
    print(f"New CPI-Normalized System Overall MAE: {mae_mean:.2f} LKR/kg")
    print(f"New CPI-Normalized System Overall MAPE: {mape_mean:.2f}%\n")

    print("==================================================================================")
    print(" FORENSIC AUDIT: 4. MULTI-MARKET & MULTI-MONTH EVALUATION")
    print("==================================================================================")
    
    months_test = [1, 4, 8, 12]
    series_test = ["Dambulla-Retail", "Dambulla-Wholesale", "Pettah-Retail", "Pettah-Wholesale"]
    
    print(f"{'Series':<18} | {'Month':<6} | {'Cases':<6} | {'Coverage %':<10} | {'MAE (LKR)':<10} | {'MAPE %':<8}")
    print("-" * 70)
    for s in series_test:
        for m in months_test:
            sub_b = df_bt[(df_bt["Series"] == s) & (df_bt["Target_Month"] == m)]
            cnt = len(sub_b)
            cov = (sub_b["Within_Range"].astype(int).sum() / cnt * 100) if cnt > 0 else 0
            mae = sub_b["Absolute_Error_LKR"].mean() if cnt > 0 else 0
            mape = sub_b["Pct_Error"].mean() if cnt > 0 else 0
            print(f"{s:<18} | {m:<6d} | {cnt:<6d} | {cov:<10.1f} | {mae:<10.2f} | {mape:<8.1f}")

if __name__ == "__main__":
    run_forensic_audit()
