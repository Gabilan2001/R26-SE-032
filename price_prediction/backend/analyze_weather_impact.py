import json
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets"
PRICE_DATA_PATH = DATASET_DIR / "tomato_prices_vegetablesSriLanka.csv"
WEATHER_CSV_PATH = DATASET_DIR / "historical_weather_sri_lanka.csv"

# 1. Location definitions
LOCATIONS = {
    "Nuwara Eliya": {"lat": 6.9497, "lon": 80.7891, "zone": "Hill-Country Supply"},
    "Badulla": {"lat": 6.9934, "lon": 81.0550, "zone": "Hill-Country Supply"},
    "Anuradhapura": {"lat": 8.3114, "lon": 80.4037, "zone": "Dry-Zone Supply"},
    "Dambulla": {"lat": 7.8567, "lon": 80.6517, "zone": "Dry-Zone Supply / Collection Hub"},
}

START_DATE = "2016-08-01"
END_DATE = "2026-03-10"


def fetch_weather_data():
    """Fetch historical weather for all 4 locations and save to CSV."""
    print("=" * 70)
    print(" FETCHING HISTORICAL WEATHER DATA FROM OPEN-METEO ARCHIVE API")
    print(f" Date range: {START_DATE} to {END_DATE}")
    print("=" * 70)

    all_weather_records = []

    for loc_name, coords in LOCATIONS.items():
        print(f" -> Fetching {loc_name} ({coords['zone']})...")
        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={coords['lat']}&longitude={coords['lon']}&"
            f"start_date={START_DATE}&end_date={END_DATE}&"
            f"daily=precipitation_sum,temperature_2m_mean&"
            f"timezone=auto"
        )

        try:
            req = urllib.request.urlopen(url)
            data = json.loads(req.read().decode("utf-8"))
            daily_data = data["daily"]

            dates = daily_data["time"]
            precip = daily_data["precipitation_sum"]
            temp = daily_data["temperature_2m_mean"]

            for d, p, t in zip(dates, precip, temp):
                all_weather_records.append(
                    {
                        "Date": d,
                        "Location": loc_name,
                        "Rainfall(mm)": p if p is not None else 0.0,
                        "Temperature(°C)": t if t is not None else np.nan,
                    }
                )
            print(f"    Success! Downloaded {len(dates)} daily records for {loc_name}.")
        except Exception as e:
            print(f"    ERROR fetching weather for {loc_name}: {e}")
            raise e

    weather_df = pd.DataFrame(all_weather_records)

    cleaned_dfs = []
    for loc_name, group in weather_df.groupby("Location"):
        group = group.sort_values("Date").reset_index(drop=True)
        group["Temperature(°C)"] = group["Temperature(°C)"].interpolate(method="linear", limit_direction="both")
        cleaned_dfs.append(group)

    weather_df = pd.concat(cleaned_dfs, ignore_index=True)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    weather_df.to_csv(WEATHER_CSV_PATH, index=False)
    print(f"\nSaved combined weather dataset to: {WEATHER_CSV_PATH.name}")
    print(f"Total weather rows saved: {len(weather_df)}")
    return weather_df


def load_price_data():
    """Load and clean tomato price dataset."""
    if not PRICE_DATA_PATH.is_file():
        raise FileNotFoundError(f"Price dataset not found at: {PRICE_DATA_PATH}")

    df = pd.read_csv(PRICE_DATA_PATH)
    df.columns = [col.strip() for col in df.columns]

    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    cleaned_series = {}
    series_combinations = [
        ("Dambulla", "Retail"),
        ("Dambulla", "Wholesale"),
        ("Pettah", "Retail"),
        ("Pettah", "Wholesale"),
    ]

    for market, s_type in series_combinations:
        sub = df[(df["Market"] == market) & (df["Type"] == s_type)].copy()
        sub = sub.sort_values("Date").reset_index(drop=True)
        sub["Price"] = pd.to_numeric(sub["Price"], errors="coerce")
        sub["Price"] = sub["Price"].interpolate(method="linear", limit_direction="both")
        label = f"{market}-{s_type}"
        cleaned_series[label] = sub[["Date", "Price"]].copy()

    return cleaned_series


def run_exploratory_correlation_analysis(weather_df, price_series_dict):
    """Run multi-lag correlation analysis between weather features and tomato prices."""
    print("\n" + "=" * 70)
    print(" EXPLORATORY CORRELATION ANALYSIS: WEATHER LAGS VS. TOMATO PRICES")
    print("=" * 70)

    lags = [0, 1, 3, 7, 14, 21, 30]
    cum_windows = [7, 14, 30]

    all_correlation_results = []

    for series_label, p_df in price_series_dict.items():
        for loc_name in LOCATIONS.keys():
            w_loc = weather_df[weather_df["Location"] == loc_name].copy()
            w_loc = w_loc.sort_values("Date").reset_index(drop=True)

            for w in cum_windows:
                w_loc[f"Rainfall_Cum_{w}d"] = w_loc["Rainfall(mm)"].rolling(window=w, min_periods=1).sum()

            merged = pd.merge(p_df, w_loc, on="Date", how="inner")

            for lag in lags:
                shifted_rain = merged["Rainfall(mm)"].shift(lag)
                shifted_temp = merged["Temperature(°C)"].shift(lag)

                valid_rain = pd.DataFrame({"Price": merged["Price"], "Rainfall": shifted_rain}).dropna()
                valid_temp = pd.DataFrame({"Price": merged["Price"], "Temp": shifted_temp}).dropna()

                r_rain = valid_rain["Price"].corr(valid_rain["Rainfall"], method="pearson")
                rho_rain = valid_rain["Price"].corr(valid_rain["Rainfall"], method="spearman")

                r_temp = valid_temp["Price"].corr(valid_temp["Temp"], method="pearson")
                rho_temp = valid_temp["Price"].corr(valid_temp["Temp"], method="spearman")

                all_correlation_results.append(
                    {
                        "Series": series_label,
                        "Location": loc_name,
                        "Feature": "Daily Rainfall",
                        "Lag": f"{lag} days",
                        "Pearson_r": r_rain,
                        "Spearman_rho": rho_rain,
                    }
                )

                all_correlation_results.append(
                    {
                        "Series": series_label,
                        "Location": loc_name,
                        "Feature": "Daily Temperature",
                        "Lag": f"{lag} days",
                        "Pearson_r": r_temp,
                        "Spearman_rho": rho_temp,
                    }
                )

            for w in cum_windows:
                for lag in [0, 7, 14]:
                    shifted_cum = merged[f"Rainfall_Cum_{w}d"].shift(lag)
                    valid_cum = pd.DataFrame({"Price": merged["Price"], "CumRain": shifted_cum}).dropna()
                    r_cum = valid_cum["Price"].corr(valid_cum["CumRain"], method="pearson")
                    rho_cum = valid_cum["Price"].corr(valid_cum["CumRain"], method="spearman")

                    all_correlation_results.append(
                        {
                            "Series": series_label,
                            "Location": loc_name,
                            "Feature": f"Cum Rain ({w}d)",
                            "Lag": f"{lag} days",
                            "Pearson_r": r_cum,
                            "Spearman_rho": rho_cum,
                        }
                    )

    results_df = pd.DataFrame(all_correlation_results)

    print("\n" + "=" * 80)
    print(" SUMMARY: TOP WEATHER-PRICE CORRELATION SIGNALS PER SERIES (RAW LEVELS)")
    print("=" * 80)

    for series_label in price_series_dict.keys():
        sub_res = results_df[results_df["Series"] == series_label].copy()
        sub_res["abs_r"] = sub_res["Pearson_r"].abs()
        top_res = sub_res.sort_values("abs_r", ascending=False).head(5)

        print(f"\n>>> Series: {series_label} Top 5 Strongest Correlations:")
        for idx, row in top_res.iterrows():
            direction = "Positive (+)" if row["Pearson_r"] > 0 else "Negative (-)"
            print(
                f"   - {row['Location']:<13} | {row['Feature']:<18} | Lag: {row['Lag']:<7} | "
                f"r = {row['Pearson_r']:+.4f} | rho = {row['Spearman_rho']:+.4f} ({direction})"
            )

    return results_df


def run_spurious_correlation_robustness_check(weather_df, price_series_dict):
    """Run autocorrelation check and differenced correlation analysis to diagnose spurious correlation."""
    print("\n" + "=" * 80)
    print(" SPURIOUS CORRELATION DIAGNOSTIC & FIRST-DIFFERENCE ROBUSTNESS CHECK")
    print(" Signal Evaluated: Anuradhapura 30-Day Cumulative Rainfall (14-Day Lag) vs. Price")
    print("=" * 80)

    # 1. Weather feature autocorrelation
    anu_w = weather_df[weather_df["Location"] == "Anuradhapura"].copy()
    anu_w = anu_w.sort_values("Date").reset_index(drop=True)
    anu_w["CumRain_30d"] = anu_w["Rainfall(mm)"].rolling(window=30, min_periods=1).sum()

    w_autocorr_1 = anu_w["CumRain_30d"].autocorr(lag=1)
    w_autocorr_7 = anu_w["CumRain_30d"].autocorr(lag=7)
    w_autocorr_14 = anu_w["CumRain_30d"].autocorr(lag=14)

    print(f"\n[1] Autocorrelation of Anuradhapura 30-Day Cumulative Rainfall:")
    print(f"    Lag-1 : {w_autocorr_1:.4f} (High persistence)")
    print(f"    Lag-7 : {w_autocorr_7:.4f}")
    print(f"    Lag-14: {w_autocorr_14:.4f}")

    print(f"\n[2] Autocorrelation of Raw Tomato Price Series (Lag-1, Lag-7, Lag-14):")
    for s_label, p_df in price_series_dict.items():
        p1 = p_df["Price"].autocorr(lag=1)
        p7 = p_df["Price"].autocorr(lag=7)
        p14 = p_df["Price"].autocorr(lag=14)
        print(f"    {s_label:<18} | Lag-1: {p1:.4f} | Lag-7: {p7:.4f} | Lag-14: {p14:.4f}")

    print("\n" + "-" * 80)
    print(f"{'Series':<18} | {'Raw r':<7} {'Raw rho':<7} | {'d1 r':<7} {'d1 rho':<7} | {'d7 r':<7} {'d7 rho':<7} | {'d14 r':<7} {'d14 rho':<7}")
    print("-" * 80)

    diff_rows = []
    for s_label, p_df in price_series_dict.items():
        merged = pd.merge(p_df, anu_w[["Date", "CumRain_30d"]], on="Date", how="inner")
        merged["CumRain_30d_lag14"] = merged["CumRain_30d"].shift(14)

        # Raw correlation
        v_raw = merged[["Price", "CumRain_30d_lag14"]].dropna()
        r_raw = v_raw["Price"].corr(v_raw["CumRain_30d_lag14"], method="pearson")
        rho_raw = v_raw["Price"].corr(v_raw["CumRain_30d_lag14"], method="spearman")

        # 1-day differences
        merged["d1_Price"] = merged["Price"].diff(1)
        merged["d1_CumRain"] = merged["CumRain_30d_lag14"].diff(1)
        v_d1 = merged[["d1_Price", "d1_CumRain"]].dropna()
        r_d1 = v_d1["d1_Price"].corr(v_d1["d1_CumRain"], method="pearson")
        rho_d1 = v_d1["d1_Price"].corr(v_d1["d1_CumRain"], method="spearman")

        # 7-day differences (week-over-week)
        merged["d7_Price"] = merged["Price"].diff(7)
        merged["d7_CumRain"] = merged["CumRain_30d_lag14"].diff(7)
        v_d7 = merged[["d7_Price", "d7_CumRain"]].dropna()
        r_d7 = v_d7["d7_Price"].corr(v_d7["d7_CumRain"], method="pearson")
        rho_d7 = v_d7["d7_Price"].corr(v_d7["d7_CumRain"], method="spearman")

        # 14-day differences (2-week changes)
        merged["d14_Price"] = merged["Price"].diff(14)
        merged["d14_CumRain"] = merged["CumRain_30d_lag14"].diff(14)
        v_d14 = merged[["d14_Price", "d14_CumRain"]].dropna()
        r_d14 = v_d14["d14_Price"].corr(v_d14["d14_CumRain"], method="pearson")
        rho_d14 = v_d14["d14_Price"].corr(v_d14["d14_CumRain"], method="spearman")

        diff_rows.append(
            {
                "Series": s_label,
                "Raw_r": r_raw,
                "Raw_rho": rho_raw,
                "d1_r": r_d1,
                "d1_rho": rho_d1,
                "d7_r": r_d7,
                "d7_rho": rho_d7,
                "d14_r": r_d14,
                "d14_rho": rho_d14,
            }
        )

        print(
            f"{s_label:<18} | {r_raw:+.4f} {rho_raw:+.4f} | {r_d1:+.4f} {rho_d1:+.4f} | {r_d7:+.4f} {rho_d7:+.4f} | {r_d14:+.4f} {rho_d14:+.4f}"
        )

    print("-" * 80)
    return pd.DataFrame(diff_rows)


def run_differenced_linear_regression(weather_df, price_series_dict):
    """Fit 14-day differenced linear regression and calculate rainfall anomaly thresholds with correct SD units."""
    print("\n" + "=" * 90)
    print(" 14-DAY DIFFERENCED LINEAR REGRESSION & ANOMALY THRESHOLDS (CORRECTED SD UNITS)")
    print(" Equation: d14_Price(t) = beta_0 + beta_1 * d14_CumRain(t-14)")
    print("=" * 90)

    from scipy import stats
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score

    anu_w = weather_df[weather_df["Location"] == "Anuradhapura"].copy()
    anu_w = anu_w.sort_values("Date").reset_index(drop=True)
    anu_w["CumRain_30d"] = anu_w["Rainfall(mm)"].rolling(window=30, min_periods=1).sum()
    anu_w["d14_CumRain"] = anu_w["CumRain_30d"].diff(14)

    raw_mean = anu_w["CumRain_30d"].mean()
    raw_sd = anu_w["CumRain_30d"].std()
    diff14_sd = anu_w["d14_CumRain"].std()

    thresh_1sd_level = raw_mean + raw_sd
    thresh_2sd_level = raw_mean + 2 * raw_sd

    print(f" Anuradhapura Historical Baseline & SD Units:")
    print(f"   - Raw 30-Day Cumulative Rain Mean (Level)    : {raw_mean:.2f} mm")
    print(f"   - Raw Level Standard Deviation (sigma_raw)    : {raw_sd:.2f} mm")
    print(f"   - Differenced 14-Day Rain Change SD (sigma_d14): {diff14_sd:.2f} mm (CORRECT REGRESSOR SD)")
    print(f"   - Anomaly Detection Flag (> Mean+1*sigma_raw): {thresh_1sd_level:.2f} mm")
    print(f"   - Anomaly Detection Flag (> Mean+2*sigma_raw): {thresh_2sd_level:.2f} mm")

    regression_results = []
    print("\n" + "-" * 95)
    print(f"{'Series':<18} | {'Slope beta_1':<12} | {'Incorrect (+1SD_raw)':<20} | {'CORRECT (+1SD_d14)':<20} | {'CORRECT (+2SD_d14)':<20}")
    print("-" * 95)

    for s_label, p_df in price_series_dict.items():
        merged = pd.merge(p_df, anu_w[["Date", "CumRain_30d"]], on="Date", how="inner")
        merged["CumRain_30d_lag14"] = merged["CumRain_30d"].shift(14)

        merged["d14_Price"] = merged["Price"].diff(14)
        merged["d14_CumRain_lag14"] = merged["CumRain_30d_lag14"].diff(14)

        valid_data = merged[["d14_Price", "d14_CumRain_lag14"]].dropna()
        X = valid_data[["d14_CumRain_lag14"]].values
        y = valid_data["d14_Price"].values

        model = LinearRegression()
        model.fit(X, y)

        beta_1 = model.coef_[0]
        beta_0 = model.intercept_
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)

        residuals = y - y_pred
        res_mean = np.mean(residuals)
        res_std = np.std(residuals)
        res_skew = stats.skew(residuals)
        res_kurt = stats.kurtosis(residuals)

        incorrect_1sd = beta_1 * raw_sd
        correct_1sd = beta_1 * diff14_sd
        correct_2sd = beta_1 * (2 * diff14_sd)

        regression_results.append(
            {
                "Series": s_label,
                "Beta_1 (LKR/mm)": beta_1,
                "Beta_0 (Intercept)": beta_0,
                "R2": r2,
                "sigma_raw (mm)": raw_sd,
                "sigma_d14 (mm)": diff14_sd,
                "Incorrect_Impact_+1SD_raw (LKR)": incorrect_1sd,
                "Correct_Impact_+1SD_d14 (LKR)": correct_1sd,
                "Correct_Impact_+2SD_d14 (LKR)": correct_2sd,
            }
        )

        print(
            f"{s_label:<18} | {beta_1:+.6f} LKR/mm | {incorrect_1sd:+.2f} LKR (+126.7mm) | {correct_1sd:+.2f} LKR (+{diff14_sd:.1f}mm) | {correct_2sd:+.2f} LKR (+{2*diff14_sd:.1f}mm)"
        )

    print("-" * 95)
    return pd.DataFrame(regression_results)



def run_decision_rule_trigger_frequency(weather_df, price_series_dict):
    """Compute historical trigger frequency for the unified 14-day rainfall change decision rule."""
    print("\n" + "=" * 90)
    print(" HISTORICAL ANOMALY TRIGGER FREQUENCY ANALYSIS (UNIFIED d14_CumRain RULE)")
    print(" Flag Condition: |d14_CumRain(t-14)| > 1 * sigma_d14 (91.05 mm)")
    print("=" * 90)

    anu_w = weather_df[weather_df["Location"] == "Anuradhapura"].copy()
    anu_w = anu_w.sort_values("Date").reset_index(drop=True)
    anu_w["CumRain_30d"] = anu_w["Rainfall(mm)"].rolling(window=30, min_periods=1).sum()
    anu_w["d14_CumRain"] = anu_w["CumRain_30d"].diff(14)

    sigma_d14 = anu_w["d14_CumRain"].std()
    thresh_1sd = sigma_d14
    thresh_2sd = 2 * sigma_d14

    freq_results = []
    print(f"\n{'Series':<18} | {'Total Days':<10} | {'Any Flag (>1SD)':<18} | {'Wet Flag (>+1SD)':<18} | {'Severe Wet (>+2SD)':<18}")
    print("-" * 90)

    for s_label, p_df in price_series_dict.items():
        merged = pd.merge(p_df, anu_w[["Date", "CumRain_30d"]], on="Date", how="inner")
        merged["d14_CumRain_lag14"] = merged["CumRain_30d"].shift(14).diff(14)

        valid_df = merged.dropna(subset=["d14_CumRain_lag14"]).copy()
        n_days = len(valid_df)

        any_flag = np.abs(valid_df["d14_CumRain_lag14"]) > thresh_1sd
        wet_flag = valid_df["d14_CumRain_lag14"] > thresh_1sd
        mod_wet_flag = (valid_df["d14_CumRain_lag14"] > thresh_1sd) & (valid_df["d14_CumRain_lag14"] <= thresh_2sd)
        sev_wet_flag = valid_df["d14_CumRain_lag14"] > thresh_2sd
        dry_flag = valid_df["d14_CumRain_lag14"] < -thresh_1sd

        freq_results.append(
            {
                "Series": s_label,
                "Total_Days": n_days,
                "Any_Flag_Count": any_flag.sum(),
                "Any_Flag_Pct": any_flag.mean() * 100,
                "Wet_Flag_Count": wet_flag.sum(),
                "Wet_Flag_Pct": wet_flag.mean() * 100,
                "Mod_Wet_Count": mod_wet_flag.sum(),
                "Mod_Wet_Pct": mod_wet_flag.mean() * 100,
                "Sev_Wet_Count": sev_wet_flag.sum(),
                "Sev_Wet_Pct": sev_wet_flag.mean() * 100,
                "Dry_Flag_Count": dry_flag.sum(),
                "Dry_Flag_Pct": dry_flag.mean() * 100,
            }
        )

        print(
            f"{s_label:<18} | {n_days:<10} | "
            f"{any_flag.sum():>3} ({any_flag.mean()*100:5.2f}%)       | "
            f"{wet_flag.sum():>3} ({wet_flag.mean()*100:5.2f}%)       | "
            f"{sev_wet_flag.sum():>3} ({sev_wet_flag.mean()*100:5.2f}%)"
        )

    print("-" * 90)
    return pd.DataFrame(freq_results)


def main():
    if WEATHER_CSV_PATH.is_file():
        print(f"Found existing weather CSV at: {WEATHER_CSV_PATH.name}. Loading...")
        weather_df = pd.read_csv(WEATHER_CSV_PATH)
    else:
        weather_df = fetch_weather_data()

    price_series_dict = load_price_data()

    # 1. Raw exploratory correlation analysis
    results_df = run_exploratory_correlation_analysis(weather_df, price_series_dict)
    corr_csv_path = DATASET_DIR / "weather_price_correlation_matrix.csv"
    results_df.to_csv(corr_csv_path, index=False)

    # 2. Spurious correlation robustness check
    diff_df = run_spurious_correlation_robustness_check(weather_df, price_series_dict)
    diff_csv_path = DATASET_DIR / "weather_differenced_robustness_matrix.csv"
    diff_df.to_csv(diff_csv_path, index=False)

    # 3. Differenced linear regression & anomaly thresholds
    reg_df = run_differenced_linear_regression(weather_df, price_series_dict)
    reg_csv_path = DATASET_DIR / "weather_regression_summary.csv"
    reg_df.to_csv(reg_csv_path, index=False)

    # 4. Trigger frequency analysis for unified decision rule
    freq_df = run_decision_rule_trigger_frequency(weather_df, price_series_dict)
    freq_csv_path = DATASET_DIR / "weather_decision_rule_frequencies.csv"
    freq_df.to_csv(freq_csv_path, index=False)

    print("\nAnalysis complete. All regression, robustness, and trigger frequency results saved.")


if __name__ == "__main__":
    main()


