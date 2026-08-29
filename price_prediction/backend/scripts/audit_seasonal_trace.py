"""
READ-ONLY Audit Script: Technical Trace of Seasonal Price Outlook.
Extracts underlying historical price observations, exact percentile formulas,
trend adjustment math, backtest accuracy records, and weather outlook logic
for Dambulla-Wholesale December 2026.
"""

from pathlib import Path
import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

PRICE_CSV = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
BACKTEST_CSV = BASE_DIR / "ml_models" / "seasonal_backtest_results.csv"
WEATHER_CSV = BASE_DIR / "datasets" / "historical_weather_sri_lanka.csv"

def audit_seasonal_details():
    print("==================================================================================")
    print(" 3. HISTORICAL DATASET & OBSERVATION AUDIT FOR DAMBULLA-WHOLESALE DECEMBER")
    print("==================================================================================\n")

    df_p = pd.read_csv(PRICE_CSV)
    df_p.columns = [c.strip() for c in df_p.columns]
    print(f"Total Rows in Price CSV before filtering: {len(df_p)}")
    
    # Market & Type filter
    sub = df_p[(df_p["Market"] == "Dambulla") & (df_p["Type"] == "Wholesale")].copy()
    print(f"Total Rows for Dambulla-Wholesale: {len(sub)}")
    
    sub["Date"] = pd.to_datetime(sub["Date"])
    sub["Price"] = pd.to_numeric(sub["Price"], errors="coerce")
    sub = sub.sort_values("Date").reset_index(drop=True)
    
    # Interpolation step
    sub["Price"] = sub["Price"].interpolate(method="linear", limit_direction="both")
    sub["Month"] = sub["Date"].dt.month
    sub["Year"] = sub["Date"].dt.year
    
    # Filter Month = 12 (December)
    sub_dec = sub[sub["Month"] == 12].copy()
    print(f"Total December Rows across all available years: {len(sub_dec)}")
    print(f"Years Present in December Subset: {sorted(sub_dec['Year'].unique().tolist())}")
    print(f"Date Range of December Subset: {sub_dec['Date'].min().strftime('%Y-%m-%d')} to {sub_dec['Date'].max().strftime('%Y-%m-%d')}\n")

    print("Decile Breakdown & Count per December Year:")
    for yr, grp in sub_dec.groupby("Year"):
        print(f"  - {yr}: {len(grp)} days, Min={grp['Price'].min():.1f}, Median={grp['Price'].median():.1f}, Max={grp['Price'].max():.1f}")

    print("\n==================================================================================")
    print(" 4. EXACT PERCENTILE REPRODUCTION (UNADJUSTED HISTORICAL PERCENTILES)")
    print("==================================================================================")
    prices = sub_dec["Price"].values
    
    p10_np = np.percentile(prices, 10)
    p25_np = np.percentile(prices, 25)
    p50_np = np.median(prices)
    p75_np = np.percentile(prices, 75)
    p90_np = np.percentile(prices, 90)

    print(f"Numpy np.percentile default (linear interpolation):")
    print(f"  Raw P10    : {p10_np:.2f}")
    print(f"  Raw P25    : {p25_np:.2f}")
    print(f"  Raw Median : {p50_np:.2f}")
    print(f"  Raw P75    : {p75_np:.2f}")
    print(f"  Raw P90    : {p90_np:.2f}")

    print("\n==================================================================================")
    print(" 5. EXACT TREND ADJUSTMENT AUDIT (+20%)")
    print("==================================================================================")
    recent_30d = sub.tail(30)
    recent_median = float(recent_30d["Price"].median())
    recent_last_date = recent_30d["Date"].iloc[-1].strftime("%Y-%m-%d")
    recent_m = recent_30d["Date"].iloc[-1].month
    
    sub_recent_m = sub[sub["Month"] == recent_m]
    hist_recent_median = float(sub_recent_m["Price"].median())
    
    raw_trend_pct = ((recent_median - hist_recent_median) / hist_recent_median) * 100.0
    capped_trend_pct = max(-20.0, min(20.0, raw_trend_pct))
    
    print(f"Recent 30 Days Date Range: {recent_30d['Date'].min().strftime('%Y-%m-%d')} to {recent_last_date}")
    print(f"Recent 30 Days Calendar Month: {recent_m} (August)")
    print(f"Recent 30 Days Median Price: {recent_median:.2f} LKR/kg")
    print(f"Historical Median Price for Month {recent_m} (August) across all years: {hist_recent_median:.2f} LKR/kg")
    print(f"Raw Trend Percentage Calculation: (({recent_median:.2f} - {hist_recent_median:.2f}) / {hist_recent_median:.2f}) * 100 = {raw_trend_pct:.2f}%")
    print(f"Capped Trend Adjustment (+/- 20% max): {capped_trend_pct:.2f}%")

    adj_factor = 1.0 + (capped_trend_pct / 100.0)
    print(f"\nAdjusted Percentiles applying factor {adj_factor:.2f}:")
    print(f"  Adjusted P10 (51.8 expected)   : {p10_np * adj_factor:.2f} -> round(1) = {round(p10_np * adj_factor, 1)}")
    print(f"  Adjusted P25 (108 expected)    : {p25_np * adj_factor:.2f} -> round(1) = {round(p25_np * adj_factor, 1)}")
    print(f"  Adjusted Median (186 expected) : {p50_np * adj_factor:.2f} -> round(1) = {round(p50_np * adj_factor, 1)}")
    print(f"  Adjusted P75 (346.5 expected)  : {p75_np * adj_factor:.2f} -> round(1) = {round(p75_np * adj_factor, 1)}")
    print(f"  Adjusted P90 (490.8 expected)  : {p90_np * adj_factor:.2f} -> round(1) = {round(p90_np * adj_factor, 1)}")

    print("\n==================================================================================")
    print(" 6. EXACT ACCURACY / CONFIDENCE LOOKUP (37.5%)")
    print("==================================================================================")
    if BACKTEST_CSV.exists():
        df_bt = pd.read_csv(BACKTEST_CSV)
        sub_bt = df_bt[(df_bt["Series"] == "Dambulla-Wholesale") & (df_bt["Target_Month"] == 12)]
        print(f"Backtest CSV Records for Dambulla-Wholesale Month 12 (December):")
        print(sub_bt[["Target_Year", "Pretend_Today", "Adjusted_Low", "Adjusted_Median", "Adjusted_High", "Actual_Median", "Within_Range", "Absolute_Error_LKR"]])
        
        within_sum = sub_bt["Within_Range"].astype(int).sum()
        total_test_years = len(sub_bt)
        within_pct = (within_sum / total_test_years) * 100.0
        print(f"\nWithin Range Count: {within_sum} / {total_test_years} test years")
        print(f"Exact Calculated Accuracy Pct: {within_pct:.1f}%")
        print(f"Confidence Mapping Rule: {within_pct:.1f}% >= 35.0% and < 50.0% -> 'MODERATE'")

if __name__ == "__main__":
    audit_seasonal_details()
