"""
Standalone Phase 2 Experiments Script for Seasonal Price Forecasting.
Tests and compares Candidate Model Architectures out-of-sample across 376 walk-forward test cases (2018-2025).

READ-ONLY to production code and datasets.
Outputs comparative metrics: Core Coverage (P25-P75), Wider Coverage (P10-P90), MAE, MAPE, and Interval Width.
"""

from pathlib import Path
import os
import sys
import pandas as pd
import numpy as np
from scipy import stats

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

PRICE_CSV_PATH = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
CPI_CSV_PATH = BASE_DIR / "datasets" / "sri_lanka_cpi.csv"
WEATHER_CSV_PATH = BASE_DIR / "datasets" / "historical_weather_sri_lanka.csv"

SERIES_LIST = [
    ("Dambulla", "Retail"),
    ("Dambulla", "Wholesale"),
    ("Pettah", "Retail"),
    ("Pettah", "Wholesale"),
]

TARGET_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def weighted_percentile(arr: np.ndarray, weights: np.ndarray, p: float) -> float:
    """Computes statistically valid weighted percentile using cumulative weight interpolation."""
    sorter = np.argsort(arr)
    arr_sorted = arr[sorter]
    weights_sorted = weights[sorter]

    cum_weights = np.cumsum(weights_sorted)
    if cum_weights[-1] == 0:
        return float(np.percentile(arr, p))
    
    cum_weights = (cum_weights - 0.5 * weights_sorted) / cum_weights[-1]
    return float(np.interp(p / 100.0, cum_weights, arr_sorted))


def load_dataset() -> pd.DataFrame:
    df_p = pd.read_csv(PRICE_CSV_PATH)
    df_p.columns = [c.strip() for c in df_p.columns]
    df_p["Date"] = pd.to_datetime(df_p["Date"])
    df_p["Price"] = pd.to_numeric(df_p["Price"], errors="coerce")
    df_p = df_p.sort_values(["Market", "Type", "Date"]).reset_index(drop=True)

    dfs = []
    for (m, t), group in df_p.groupby(["Market", "Type"]):
        group = group.copy()
        group["Price"] = group["Price"].interpolate(method="linear", limit_direction="both")
        dfs.append(group)

    full_df = pd.concat(dfs, ignore_index=True)
    full_df["YearMonth"] = full_df["Date"].dt.strftime("%Y-%m")
    full_df["Year"] = full_df["Date"].dt.year
    full_df["Month"] = full_df["Date"].dt.month

    df_cpi = pd.read_csv(CPI_CSV_PATH)
    df_cpi["YearMonth"] = df_cpi["YearMonth"].astype(str).str.strip()
    latest_cpi = float(df_cpi.iloc[-1]["CCPI"])

    full_df = pd.merge(full_df, df_cpi, on="YearMonth", how="left")
    full_df["CCPI"] = full_df["CCPI"].fillna(latest_cpi)
    full_df["Real_Price"] = full_df["Price"] * (latest_cpi / full_df["CCPI"])
    return full_df, latest_cpi


def load_weather_dataset() -> pd.DataFrame:
    df_w = pd.read_csv(WEATHER_CSV_PATH)
    df_w["Date"] = pd.to_datetime(df_w["Date"])
    return df_w


def run_phase2_experiments():
    print("==================================================================================")
    print(" PHASE 2 EXPERIMENTS: RECENCY WEIGHTING, TREND BOUNDS & WEATHER PREDICTABILITY")
    print("==================================================================================\n")

    df, latest_cpi = load_dataset()
    df_w = load_weather_dataset()

    # ----------------------------------------------------------------------------------
    # EXPERIMENT 1: Recency Weighting Analysis
    # ----------------------------------------------------------------------------------
    print("1. RECENCY WEIGHTING RELATIVE WEIGHT DECAY TABLE (lambda = 0.15):")
    max_yr = 2025
    years_sample = [2016, 2018, 2020, 2022, 2024, 2025]
    for yr in years_sample:
        w = np.exp(0.15 * (yr - max_yr))
        rel_w = w / np.exp(0.15 * (2025 - max_yr)) * 100.0
        print(f"  - Year {yr}: Weight = {w:.4f} (Relative to 2025 = {rel_w:5.1f}%)")
    print()

    # ----------------------------------------------------------------------------------
    # EXPERIMENT 3: Weather Predictability Test (Lagged Rainfall Anomalies vs Future Real Prices)
    # ----------------------------------------------------------------------------------
    print("2. WEATHER PREDICTABILITY ANALYSIS (Lagged Rainfall Anomalies vs 30-60d Price Changes):")
    weather_corrs = []
    for station in ["Anuradhapura", "Badulla", "Dambulla", "Nuwara Eliya"]:
        sub_w = df_w[df_w["Location"] == station].sort_values("Date").reset_index(drop=True)
        # 30-day lagged rain anomaly
        sub_w["Rain_30d"] = sub_w["Rainfall(mm)"].rolling(30).sum()
        sub_w["Month"] = sub_w["Date"].dt.month
        
        # Merge with Dambulla Wholesale real price 60 days ahead
        sub_p = df[(df["Market"] == "Dambulla") & (df["Type"] == "Wholesale")][["Date", "Real_Price"]].copy()
        sub_p["Price_Future_60d"] = sub_p["Real_Price"].shift(-60)
        sub_p["Real_Return_60d"] = ((sub_p["Price_Future_60d"] - sub_p["Real_Price"]) / sub_p["Real_Price"]) * 100.0
        
        m_w = pd.merge(sub_w, sub_p, on="Date", how="inner").dropna(subset=["Rain_30d", "Real_Return_60d"])
        r_val, p_val = stats.pearsonr(m_w["Rain_30d"], m_w["Real_Return_60d"])
        weather_corrs.append({"Station": station, "Lag": "30d Rain -> 60d Return", "Correlation_r": round(r_val, 4), "p_value": round(p_val, 4)})
        print(f"  - Station {station:<14} (30d Rain -> 60d Price Return): r = {r_val:+0.4f}, p = {p_val:.4f} {'(NOT SIGNIFICANT)' if p_val > 0.05 else '(SIGNIFICANT)'}")
    print()

    # ----------------------------------------------------------------------------------
    # EXPERIMENT 4: Model Candidate Walk-Forward Evaluation (376 Test Cases)
    # ----------------------------------------------------------------------------------
    print("==================================================================================")
    print(" 3. OUT-OF-SAMPLE WALK-FORWARD COMPARISON OF CANDIDATE MODELS (376 TEST CASES)")
    print("==================================================================================\n")

    results_m0 = [] # Model 0: Current Upgraded (Unweighted + +/-20% Cap)
    results_m1 = [] # Model 1: CPI-Normalized + Weighted Daily Percentiles + +/-20% Cap
    results_m2 = [] # Model 2: CPI-Normalized + Weighted Percentiles + +/-1.5 Std Trend Bound
    results_m3 = [] # Model 3: Model 2 + Weather Multiplier (if significant)

    for mkt, stype in SERIES_LIST:
        series_label = f"{mkt}-{stype}"
        sub_series = df[(df["Market"] == mkt) & (df["Type"] == stype)].copy()

        for target_year in TARGET_YEARS:
            for target_month in range(1, 13):
                target_midpoint = pd.Timestamp(year=target_year, month=target_month, day=15)
                pretend_today = target_midpoint - pd.Timedelta(days=90)

                df_history = sub_series[sub_series["Date"] < pretend_today].copy()
                if df_history.empty:
                    continue

                df_target_month_hist = df_history[
                    (df_history["Month"] == target_month) & (df_history["Year"] < target_year)
                ].copy()

                if len(df_target_month_hist) < 15:
                    continue

                actual_df = sub_series[(sub_series["Year"] == target_year) & (sub_series["Month"] == target_month)]
                if actual_df.empty:
                    continue
                actual_median = float(actual_df["Price"].median())

                # Ground Truth Inflation CPI projection
                pretend_cpi = float(df_history.iloc[-1]["CCPI"])
                months_to_target = max(0, (target_midpoint.year - pretend_today.year) * 12 + (target_midpoint.month - pretend_today.month))
                target_proj_cpi = pretend_cpi * ((1.0 + 0.04) ** (months_to_target / 12.0))
                reinflate = target_proj_cpi / pretend_cpi

                # ----------------------------------------------------
                # MODEL 0: Unweighted Percentiles + +/- 20% Cap
                # ----------------------------------------------------
                real_m0_p25 = float(np.percentile(df_target_month_hist["Real_Price"], 25))
                real_m0_p50 = float(np.median(df_target_month_hist["Real_Price"]))
                real_m0_p75 = float(np.percentile(df_target_month_hist["Real_Price"], 75))
                real_m0_p10 = float(np.percentile(df_target_month_hist["Real_Price"], 10))
                real_m0_p90 = float(np.percentile(df_target_month_hist["Real_Price"], 90))

                recent_30d = df_history[df_history["Date"] >= (pretend_today - pd.Timedelta(days=30))]
                recent_real_med = float(recent_30d["Real_Price"].median()) if not recent_30d.empty else real_m0_p50
                recent_m = pretend_today.month
                sub_rec_m = df_history[df_history["Month"] == recent_m]
                hist_rec_real_med = float(sub_rec_m["Real_Price"].median()) if not sub_rec_m.empty else recent_real_med
                
                raw_trend = ((recent_real_med - hist_rec_real_med) / hist_rec_real_med) * 100.0 if hist_rec_real_med > 0 else 0.0
                m0_trend_adj = max(-20.0, min(20.0, raw_trend))
                f0 = 1.0 + (m0_trend_adj / 100.0)

                m0_nom_p25 = real_m0_p25 * f0 * reinflate
                m0_nom_p50 = real_m0_p50 * f0 * reinflate
                m0_nom_p75 = real_m0_p75 * f0 * reinflate
                m0_nom_p10 = real_m0_p10 * f0 * reinflate
                m0_nom_p90 = real_m0_p90 * f0 * reinflate

                results_m0.append({
                    "Within_Core": (m0_nom_p25 <= actual_median <= m0_nom_p75),
                    "Within_Wider": (m0_nom_p10 <= actual_median <= m0_nom_p90),
                    "MAE": abs(actual_median - m0_nom_p50),
                    "MAPE": (abs(actual_median - m0_nom_p50) / actual_median) * 100.0 if actual_median > 0 else 0,
                    "Core_Width": m0_nom_p75 - m0_nom_p25,
                })

                # ----------------------------------------------------
                # MODEL 1: Weighted Percentiles + +/- 20% Cap
                # ----------------------------------------------------
                max_h_yr = df_history["Year"].max()
                df_target_month_hist["Weight"] = np.exp(0.15 * (df_target_month_hist["Year"] - max_h_yr))
                
                real_m1_p25 = weighted_percentile(df_target_month_hist["Real_Price"].values, df_target_month_hist["Weight"].values, 25)
                real_m1_p50 = weighted_percentile(df_target_month_hist["Real_Price"].values, df_target_month_hist["Weight"].values, 50)
                real_m1_p75 = weighted_percentile(df_target_month_hist["Real_Price"].values, df_target_month_hist["Weight"].values, 75)
                real_m1_p10 = weighted_percentile(df_target_month_hist["Real_Price"].values, df_target_month_hist["Weight"].values, 10)
                real_m1_p90 = weighted_percentile(df_target_month_hist["Real_Price"].values, df_target_month_hist["Weight"].values, 90)

                m1_nom_p25 = real_m1_p25 * f0 * reinflate
                m1_nom_p50 = real_m1_p50 * f0 * reinflate
                m1_nom_p75 = real_m1_p75 * f0 * reinflate
                m1_nom_p10 = real_m1_p10 * f0 * reinflate
                m1_nom_p90 = real_m1_p90 * f0 * reinflate

                results_m1.append({
                    "Within_Core": (m1_nom_p25 <= actual_median <= m1_nom_p75),
                    "Within_Wider": (m1_nom_p10 <= actual_median <= m1_nom_p90),
                    "MAE": abs(actual_median - m1_nom_p50),
                    "MAPE": (abs(actual_median - m1_nom_p50) / actual_median) * 100.0 if actual_median > 0 else 0,
                    "Core_Width": m1_nom_p75 - m1_nom_p25,
                })

                # ----------------------------------------------------
                # MODEL 2: Weighted Percentiles + Dynamic Std Trend Bound (+/- 1.5 Std)
                # ----------------------------------------------------
                # Compute historical monthly trend std in df_history
                hist_month_returns = []
                for yr_h in df_history["Year"].unique():
                    sub_y = df_history[df_history["Year"] == yr_h]
                    m_curr = sub_y[sub_y["Month"] == recent_m]
                    if not m_curr.empty:
                        hist_month_returns.append(float(m_curr["Real_Price"].median()))
                
                if len(hist_month_returns) > 2:
                    std_trend_pct = (np.std(hist_month_returns) / np.mean(hist_month_returns)) * 100.0
                    dynamic_cap = 1.5 * std_trend_pct
                else:
                    dynamic_cap = 25.0

                m2_trend_adj = max(-dynamic_cap, min(dynamic_cap, raw_trend))
                f2 = 1.0 + (m2_trend_adj / 100.0)

                m2_nom_p25 = real_m1_p25 * f2 * reinflate
                m2_nom_p50 = real_m1_p50 * f2 * reinflate
                m2_nom_p75 = real_m1_p75 * f2 * reinflate
                m2_nom_p10 = real_m1_p10 * f2 * reinflate
                m2_nom_p90 = real_m1_p90 * f2 * reinflate

                results_m2.append({
                    "Within_Core": (m2_nom_p25 <= actual_median <= m2_nom_p75),
                    "Within_Wider": (m2_nom_p10 <= actual_median <= m2_nom_p90),
                    "MAE": abs(actual_median - m2_nom_p50),
                    "MAPE": (abs(actual_median - m2_nom_p50) / actual_median) * 100.0 if actual_median > 0 else 0,
                    "Core_Width": m2_nom_p75 - m2_nom_p25,
                })

    # Summary table output
    df_m0 = pd.DataFrame(results_m0)
    df_m1 = pd.DataFrame(results_m1)
    df_m2 = pd.DataFrame(results_m2)

    print(f"{'Model Candidate Architecture':<48} | {'Core Coverage [P25-P75]':<22} | {'Wider Coverage [P10-P90]':<23} | {'Median MAE':<12} | {'Mean MAPE':<10} | {'Avg Core Width':<14}")
    print("-" * 140)
    print(f"{'Model 0: Unweighted Percentiles + +/-20% Cap':<48} | {df_m0['Within_Core'].sum()}/{len(df_m0)} ({df_m0['Within_Core'].mean()*100:5.1f}%)         | {df_m0['Within_Wider'].sum()}/{len(df_m0)} ({df_m0['Within_Wider'].mean()*100:5.1f}%)          | {df_m0['MAE'].median():6.2f} LKR  | {df_m0['MAPE'].mean():6.1f}%  | {df_m0['Core_Width'].mean():6.1f} LKR")
    print(f"{'Model 1: Weighted Percentiles + +/-20% Cap':<48} | {df_m1['Within_Core'].sum()}/{len(df_m1)} ({df_m1['Within_Core'].mean()*100:5.1f}%)         | {df_m1['Within_Wider'].sum()}/{len(df_m1)} ({df_m1['Within_Wider'].mean()*100:5.1f}%)          | {df_m1['MAE'].median():6.2f} LKR  | {df_m1['MAPE'].mean():6.1f}%  | {df_m1['Core_Width'].mean():6.1f} LKR")
    print(f"{'Model 2: Weighted Percentiles + Dynamic 1.5 Std Cap':<48} | {df_m2['Within_Core'].sum()}/{len(df_m2)} ({df_m2['Within_Core'].mean()*100:5.1f}%)         | {df_m2['Within_Wider'].sum()}/{len(df_m2)} ({df_m2['Within_Wider'].mean()*100:5.1f}%)          | {df_m2['MAE'].median():6.2f} LKR  | {df_m2['MAPE'].mean():6.1f}%  | {df_m2['Core_Width'].mean():6.1f} LKR")

if __name__ == "__main__":
    run_phase2_experiments()
