"""
Rigorous READ-ONLY Weather-Price Statistical Validation Script.
Performs:
1. Dataset audit & verification
2. Multi-feature construction (cumulative rainfall, moving average temp, monthly Z-scores)
3. Strict lag correlation testing (Pearson r, Spearman rho, p-values)
4. Benjamini-Hochberg FDR multiple testing adjustment
5. Linear baseline vs Weather-enhanced predictive incremental value test (Out-of-sample MAE)
6. Saves results to backend/ml_models/weather_price_lag_results.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os

BASE_DIR = Path(__file__).resolve().parent.parent
WEATHER_CSV = BASE_DIR / "datasets" / "historical_weather_sri_lanka.csv"
PRICE_CSV = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
RESULTS_CSV = BASE_DIR / "ml_models" / "weather_price_lag_results.csv"

def audit_datasets():
    print("==================================================================================")
    print(" 1. INDEPENDENT DATASET AUDIT")
    print("==================================================================================\n")

    # Weather Audit
    df_w = pd.read_csv(WEATHER_CSV)
    df_w.columns = [c.strip() for c in df_w.columns]
    print(f"Weather Dataset: {WEATHER_CSV}")
    print(f"  Rows: {len(df_w)}, Cols: {list(df_w.columns)}")
    print(f"  Missing values:\n{df_w.isnull().sum().to_dict()}")
    df_w["Date"] = pd.to_datetime(df_w["Date"])
    print(f"  Date range: {df_w['Date'].min().strftime('%Y-%m-%d')} to {df_w['Date'].max().strftime('%Y-%m-%d')}")
    print(f"  Locations: {df_w['Location'].value_counts().to_dict()}")
    print(f"  Duplicate rows: {df_w.duplicated(subset=['Date', 'Location']).sum()}")

    # Price Audit
    df_p = pd.read_csv(PRICE_CSV)
    df_p.columns = [c.strip() for c in df_p.columns]
    df_tom = df_p[df_p["Item"] == "Tomato"].copy()
    df_tom["Date"] = pd.to_datetime(df_tom["Date"])
    print(f"\nPrice Dataset (Tomato filter): {PRICE_CSV}")
    print(f"  Total Tomato Rows: {len(df_tom)}")
    print(f"  Missing values:\n{df_tom.isnull().sum().to_dict()}")
    print(f"  Date range: {df_tom['Date'].min().strftime('%Y-%m-%d')} to {df_tom['Date'].max().strftime('%Y-%m-%d')}")
    series_counts = df_tom.groupby(["Market", "Type"]).size().to_dict()
    print(f"  Series row counts: {series_counts}")
    print(f"  Duplicate rows: {df_tom.duplicated(subset=['Date', 'Market', 'Type', 'Item']).sum()}")

    # Overlap Audit
    w_dates = set(df_w["Date"].dt.strftime('%Y-%m-%d'))
    p_dates = set(df_tom["Date"].dt.strftime('%Y-%m-%d'))
    overlap = w_dates.intersection(p_dates)
    print(f"\nDate Overlap:")
    print(f"  Weather unique dates: {len(w_dates)}")
    print(f"  Price unique dates: {len(p_dates)}")
    print(f"  Overlapping trading dates: {len(overlap)} (Min: {min(overlap)}, Max: {max(overlap)})")
    print("\n")

def benjamini_hochberg(p_values):
    """Computes Benjamini-Hochberg FDR q-values."""
    p_values = np.asarray(p_values)
    n = len(p_values)
    sorted_idx = np.argsort(p_values)
    sorted_p = p_values[sorted_idx]
    q_values = np.zeros(n)
    
    cummin = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        q = (sorted_p[i] * n) / rank
        if q < cummin:
            cummin = q
        q_values[i] = cummin

    # Reorder to original indices
    q_out = np.zeros(n)
    q_out[sorted_idx] = q_values
    return q_out

def run_statistical_validation():
    print("==================================================================================")
    print(" 4, 5, 6, 7, 8. STATISTICAL HYPOTHESIS TESTING WITH FDR CORRECTION")
    print("==================================================================================\n")

    # Load & Preprocess Weather
    df_w = pd.read_csv(WEATHER_CSV)
    df_w.columns = [c.strip() for c in df_w.columns]
    df_w["Date"] = pd.to_datetime(df_w["Date"])
    df_w = df_w.rename(columns={"Rainfall(mm)": "Rainfall", "Temperature(°C)": "Temperature", "Temperature(?C)": "Temperature"})
    for col in df_w.columns:
        if "Rainfall" in col:
            df_w[col] = pd.to_numeric(df_w[col], errors="coerce")
            df_w = df_w.rename(columns={col: "Rainfall"})
        elif "Temp" in col:
            df_w[col] = pd.to_numeric(df_w[col], errors="coerce")
            df_w = df_w.rename(columns={col: "Temperature"})

    df_w["Month"] = df_w["Date"].dt.month

    # Calculate Monthly Baseline Normals (Mean & Std per Location & Month)
    monthly_stats = df_w.groupby(["Location", "Month"])[["Rainfall", "Temperature"]].agg(["mean", "std"]).reset_index()
    monthly_stats.columns = ["Location", "Month", "Rainfall_mean", "Rainfall_std", "Temp_mean", "Temp_std"]

    df_w = pd.merge(df_w, monthly_stats, on=["Location", "Month"], how="left")
    df_w["Rainfall_Z"] = (df_w["Rainfall"] - df_w["Rainfall_mean"]) / (df_w["Rainfall_std"] + 1e-6)
    df_w["Temp_Z"] = (df_w["Temperature"] - df_w["Temp_mean"]) / (df_w["Temp_std"] + 1e-6)

    # Load & Preprocess Prices
    df_p = pd.read_csv(PRICE_CSV)
    df_p.columns = [c.strip() for c in df_p.columns]
    df_tom = df_p[df_p["Item"] == "Tomato"].copy()
    df_tom["Date"] = pd.to_datetime(df_tom["Date"])
    df_tom["Price"] = pd.to_numeric(df_tom["Price"], errors="coerce")

    markets = [("Dambulla", "Retail"), ("Dambulla", "Wholesale"), ("Pettah", "Retail"), ("Pettah", "Wholesale")]
    stations = df_w["Location"].unique()
    lags = [1, 3, 7, 14, 21, 30]

    test_results = []

    for m, t in markets:
        sub_p = df_tom[(df_tom["Market"] == m) & (df_tom["Type"] == t)].sort_values("Date").reset_index(drop=True)
        sub_p["Price"] = sub_p["Price"].interpolate(method="linear", limit_direction="both")
        sub_p["Price_Diff"] = sub_p["Price"].diff() # Stationary series for comparison

        for st in stations:
            sub_w = df_w[df_w["Location"] == st].sort_values("Date").reset_index(drop=True)

            # Feature Engineering on Weather
            for l in lags:
                if l == 1:
                    sub_w[f"Rain_cum_{l}d"] = sub_w["Rainfall"]
                    sub_w[f"Temp_ma_{l}d"] = sub_w["Temperature"]
                    sub_w[f"Rain_Z_{l}d"] = sub_w["Rainfall_Z"]
                    sub_w[f"Temp_Z_{l}d"] = sub_w["Temp_Z"]
                else:
                    sub_w[f"Rain_cum_{l}d"] = sub_w["Rainfall"].rolling(l, min_periods=1).sum()
                    sub_w[f"Temp_ma_{l}d"] = sub_w["Temperature"].rolling(l, min_periods=1).mean()
                    sub_w[f"Rain_Z_{l}d"] = sub_w["Rainfall_Z"].rolling(l, min_periods=1).mean()
                    sub_w[f"Temp_Z_{l}d"] = sub_w["Temp_Z"].rolling(l, min_periods=1).mean()

            # Merge on date
            merged = pd.merge(sub_p[["Date", "Price", "Price_Diff"]], sub_w, on="Date", how="inner")

            for l in lags:
                features_to_test = [
                    ("Rainfall", f"Rain_cum_{l}d", "Raw Cumulative Rain"),
                    ("Temperature", f"Temp_ma_{l}d", "Raw Moving Avg Temp"),
                    ("Rainfall_Z", f"Rain_Z_{l}d", "Seasonal Rain Anomaly Z"),
                    ("Temperature_Z", f"Temp_Z_{l}d", "Seasonal Temp Anomaly Z"),
                ]

                for var_type, feat_col, feat_desc in features_to_test:
                    # Shift feature by lag l (weather at t-l predicting price at t)
                    lagged_feat = merged[feat_col].shift(l)
                    valid_df = pd.DataFrame({"Price": merged["Price"], "Price_Diff": merged["Price_Diff"], "Feature": lagged_feat}).dropna()

                    if len(valid_df) > 100:
                        pr, p_val_pearson = stats.pearsonr(valid_df["Feature"], valid_df["Price"])
                        sr, p_val_spearman = stats.spearmanr(valid_df["Feature"], valid_df["Price"])

                        # Also calculate correlation with stationary price diff
                        pr_diff, p_val_diff = stats.pearsonr(valid_df["Feature"], valid_df["Price_Diff"])

                        test_results.append({
                            "Market_Series": f"{m}-{t}",
                            "Station": st,
                            "Variable": var_type,
                            "Feature_Desc": feat_desc,
                            "Lag_Days": l,
                            "Pearson_r": round(pr, 4),
                            "Pearson_p": p_val_pearson,
                            "Spearman_rho": round(sr, 4),
                            "Spearman_p": p_val_spearman,
                            "Diff_Pearson_r": round(pr_diff, 4),
                            "Diff_p": p_val_diff,
                            "N": len(valid_df)
                        })

    df_res = pd.DataFrame(test_results)

    # Apply FDR correction across all p-values
    df_res["FDR_q_pearson"] = benjamini_hochberg(df_res["Pearson_p"].values)
    df_res["FDR_q_spearman"] = benjamini_hochberg(df_res["Spearman_p"].values)

    df_res.to_csv(RESULTS_CSV, index=False)
    print(f"Total Hypothesis Tests Conducted: {len(df_res)}")
    print(f"Results saved to: {RESULTS_CSV}")

    # Display Top Significant Results
    sig_df = df_res[df_res["FDR_q_pearson"] < 0.05].sort_values("Pearson_r", key=abs, ascending=False)
    print(f"Statistically Significant Tests at FDR q < 0.05: {len(sig_df)} / {len(df_res)}")
    print("\n--- TOP 15 STRONGEST SIGNIFICANT WEATHER-PRICE RELATIONSHIPS ---")
    print(sig_df[["Market_Series", "Station", "Feature_Desc", "Lag_Days", "Pearson_r", "Spearman_rho", "Pearson_p", "FDR_q_pearson", "Diff_Pearson_r"]].head(15).to_string(index=False))
    print("\n")

def run_predictive_value_test():
    print("==================================================================================")
    print(" 14, 15. OUT-OF-SAMPLE PREDICTIVE VALUE BEYOND PRICE HISTORY")
    print("==================================================================================\n")

    # Load Data
    df_w = pd.read_csv(WEATHER_CSV)
    df_w.columns = [c.strip() for c in df_w.columns]
    df_w["Date"] = pd.to_datetime(df_w["Date"])
    df_w = df_w.rename(columns={"Rainfall(mm)": "Rainfall", "Temperature(°C)": "Temperature", "Temperature(?C)": "Temperature"})
    for col in df_w.columns:
        if "Rainfall" in col:
            df_w[col] = pd.to_numeric(df_w[col], errors="coerce")
            df_w = df_w.rename(columns={col: "Rainfall"})
        elif "Temp" in col:
            df_w[col] = pd.to_numeric(df_w[col], errors="coerce")
            df_w = df_w.rename(columns={col: "Temperature"})

    df_p = pd.read_csv(PRICE_CSV)
    df_p.columns = [c.strip() for c in df_p.columns]
    df_tom = df_p[df_p["Item"] == "Tomato"].copy()
    df_tom["Date"] = pd.to_datetime(df_tom["Date"])
    df_tom["Price"] = pd.to_numeric(df_tom["Price"], errors="coerce")

    # We evaluate for Dambulla-Wholesale & Pettah-Wholesale across 1, 3, 7, 14 day horizons
    horizons = [1, 3, 7, 14]
    series_list = [("Dambulla", "Wholesale"), ("Pettah", "Wholesale")]

    pred_rows = []

    for m, t in series_list:
        sub_p = df_tom[(df_tom["Market"] == m) & (df_tom["Type"] == t)].sort_values("Date").reset_index(drop=True)
        sub_p["Price"] = sub_p["Price"].interpolate(method="linear", limit_direction="both")

        # Create price lag features (lags 0 to 9)
        for i in range(10):
            sub_p[f"price_lag_{i}"] = sub_p["Price"].shift(i)

        # Merge weather features (Badulla 21d Rain & Anuradhapura 21d Rain)
        sub_w_b = df_w[df_w["Location"] == "Badulla"].sort_values("Date").copy()
        sub_w_b["rain_21d_badulla"] = sub_w_b["Rainfall"].rolling(21, min_periods=1).sum()

        sub_w_a = df_w[df_w["Location"] == "Anuradhapura"].sort_values("Date").copy()
        sub_w_a["rain_21d_anu"] = sub_w_a["Rainfall"].rolling(21, min_periods=1).sum()

        m1 = pd.merge(sub_p, sub_w_b[["Date", "rain_21d_badulla"]], on="Date", how="inner")
        m2 = pd.merge(m1, sub_w_a[["Date", "rain_21d_anu"]], on="Date", how="inner")

        for h in horizons:
            # Target is price at t+h
            m2[f"target_{h}d"] = m2["Price"].shift(-h)
            
            # Features
            price_cols = [f"price_lag_{i}" for i in range(10)]
            weather_cols = ["rain_21d_badulla", "rain_21d_anu"]
            
            clean_df = m2.dropna(subset=[f"target_{h}d"] + price_cols + weather_cols).reset_index(drop=True)

            # 80/20 Chronological Split
            split_idx = int(len(clean_df) * 0.8)
            train_df = clean_df.iloc[:split_idx]
            test_df = clean_df.iloc[split_idx:]

            X_train_base = train_df[price_cols]
            X_test_base = test_df[price_cols]

            X_train_weath = train_df[price_cols + weather_cols]
            X_test_weath = test_df[price_cols + weather_cols]

            y_train = train_df[f"target_{h}d"]
            y_test = test_df[f"target_{h}d"]

            # Train Ridge Baseline
            model_base = Ridge(alpha=1.0)
            model_base.fit(X_train_base, y_train)
            pred_base = model_base.predict(X_test_base)
            mae_base = mean_absolute_error(y_test, pred_base)

            # Train Ridge Weather-Enhanced
            model_weath = Ridge(alpha=1.0)
            model_weath.fit(X_train_weath, y_train)
            pred_weath = model_weath.predict(X_test_weath)
            mae_weath = mean_absolute_error(y_test, pred_weath)

            pct_imp = ((mae_base - mae_weath) / mae_base) * 100.0

            pred_rows.append({
                "Series": f"{m}-{t}",
                "Horizon": f"{h}d",
                "Baseline_MAE": round(mae_base, 2),
                "Weather_Enhanced_MAE": round(mae_weath, 2),
                "MAE_Improvement_LKR": round(mae_base - mae_weath, 2),
                "Pct_Improvement": round(pct_imp, 2),
                "Test_N": len(test_df)
            })

    df_pred_res = pd.DataFrame(pred_rows)
    print(df_pred_res.to_string(index=False))
    print("\n")

if __name__ == "__main__":
    audit_datasets()
    run_statistical_validation()
    run_predictive_value_test()
