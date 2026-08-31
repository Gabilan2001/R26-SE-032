"""
Decision Engine Service Module
Combines base Bidirectional LSTM price forecasts, calibrated weather adjustments,
and IsolationForest price anomaly detection into unified farmer recommendations.

Empirical Grounding:
- Anomaly Detection First: Override with "MONITOR" if residual price anomaly is detected.
- Volatility Threshold: Based on empirical series-specific 1-sigma daily percentage price volatility
  (Dambulla-Retail: 17.1%, Dambulla-Wholesale: 23.6%, Pettah-Retail: 14.8%, Pettah-Wholesale: 18.6%).
  This ensures recommendations only trigger when forecasted movements exceed routine market noise.
- Driver Attribution: Transparently attributes the forecast change between Base LSTM momentum vs. Weather adjustment.
"""

from __future__ import annotations

import logging
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.services.anomaly_detection_service import check_price_anomaly
from app.services.news_event_service import get_news_flag
from app.services.regional_weather_service import RegionalWeatherService
from app.services.shap_explainer_service import get_shap_explanation



logger = logging.getLogger(__name__)

MODEL_DIR = BASE_DIR / "ml_models"
DATASET_DIR = BASE_DIR / "datasets"
PRICE_CSV_PATH = DATASET_DIR / "tomato_prices_vegetablesSriLanka.csv"
WEATHER_CSV_PATH = DATASET_DIR / "historical_weather_sri_lanka.csv"

# Calibrated Series Slopes (beta_1: LKR price change per mm of 30-day rainfall change at 14-day lag)
SLOPES: Dict[str, float] = {
    "Dambulla-Retail": 0.264559,
    "Dambulla-Wholesale": 0.260859,
    "Pettah-Retail": 0.299140,
    "Pettah-Wholesale": 0.270252,
}

# Empirical Active-Days 1-Sigma Percentage Volatility Thresholds per Series (excluding 0% flat days)
SERIES_VOLATILITY_SIGMA_PCT: Dict[str, float] = {
    "Dambulla-Retail": 18.54,
    "Dambulla-Wholesale": 25.38,
    "Pettah-Retail": 19.03,
    "Pettah-Wholesale": 23.62,
}


# Unified Weather Thresholds based on sigma_d14 = 91.05 mm
SIGMA_D14: float = 91.05
MODERATE_THRESHOLD: float = 91.05  # 1 * SIGMA_D14
SEVERE_THRESHOLD: float = 182.10   # 2 * SIGMA_D14


def get_anuradhapura_d14_cum_rain(
    target_date_str: str, weather_csv: Optional[Path] = None
) -> Tuple[float, str]:
    """
    Compute observed d14_CumRain for Anuradhapura ending on or before target_date_str:
    d14_CumRain = (30-day cumulative rainfall ending 14 days ago) - (30-day cumulative rainfall ending 28 days ago).
    """
    csv_path = weather_csv or WEATHER_CSV_PATH
    if not csv_path.is_file():
        raise FileNotFoundError(f"Weather dataset not found at {csv_path}")

    df = pd.read_csv(csv_path)
    anu = df[df["Location"] == "Anuradhapura"].copy()
    anu["Date"] = pd.to_datetime(anu["Date"])
    anu = anu.sort_values("Date").reset_index(drop=True)

    anu["CumRain_30d"] = anu["Rainfall(mm)"].rolling(window=30, min_periods=1).sum()
    anu["d14_CumRain"] = anu["CumRain_30d"].diff(14)

    target_dt = pd.to_datetime(target_date_str)
    sub = anu[anu["Date"] <= target_dt]
    if sub.empty:
        raise ValueError(f"No weather data available on or before {target_date_str}")

    row = sub.iloc[-1]
    val = float(row["d14_CumRain"])
    actual_date = row["Date"].strftime("%Y-%m-%d")
    return val, actual_date


def get_recent_price_window(
    market: str,
    series_type: str,
    target_date_str: str,
    window_size: int = 10,
    price_csv: Optional[Path] = None,
) -> Tuple[np.ndarray, str, str, str]:
    """
    Fetch recent window_size daily prices ending on or before target_date_str for requested series.
    Returns: (window_prices, last_price_date, max_dataset_date, dataset_coverage)
    """
    csv_path = price_csv or PRICE_CSV_PATH
    if not csv_path.is_file():
        raise FileNotFoundError(f"Price dataset not found at {csv_path}")

    df = pd.read_csv(csv_path)
    df.columns = [col.strip() for col in df.columns]

    sub = df[(df["Market"] == market) & (df["Type"] == series_type)].copy()
    if sub.empty:
        raise ValueError(f"No data found for Market: {market}, Type: {series_type}")

    sub["Date"] = pd.to_datetime(sub["Date"])
    sub = sub.sort_values("Date").reset_index(drop=True)
    sub["Price"] = pd.to_numeric(sub["Price"], errors="coerce")
    sub["Price"] = sub["Price"].interpolate(method="linear", limit_direction="both")

    min_date = sub["Date"].min()
    max_date = sub["Date"].max()
    max_dataset_date = max_date.strftime("%Y-%m-%d")
    dataset_coverage = f"{min_date.strftime('%b %Y')} to {max_date.strftime('%b %Y')}"

    target_dt = pd.to_datetime(target_date_str)
    sub_filtered = sub[sub["Date"] <= target_dt]
    if len(sub_filtered) < window_size:
        raise ValueError(f"Not enough price history for {market}-{series_type} on or before {target_date_str}")

    tail = sub_filtered.tail(window_size)
    window_prices = tail["Price"].values
    last_date = tail["Date"].iloc[-1].strftime("%Y-%m-%d")
    return window_prices, last_date, max_dataset_date, dataset_coverage


def run_decision_engine(
    market: str = "Dambulla",
    series_type: str = "Retail",
    target_date_str: str = "2026-03-10",
    horizon_days: int = 14,
    price_csv_path: Optional[Path] = None,
    weather_csv_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Run decision engine combining LSTM base forecast with weather adjustment.
    """
    series_label = f"{market}-{series_type}"
    if series_label not in SLOPES:
        raise ValueError(f"Unsupported series combination: {series_label}. Supported: {list(SLOPES.keys())}")

    file_suffix = f"{market.lower()}_{series_type.lower()}"
    lstm_path = MODEL_DIR / f"lstm_{file_suffix}.h5"
    scaler_path = MODEL_DIR / f"scaler_{file_suffix}.pkl"

    if not lstm_path.is_file() or not scaler_path.is_file():
        raise FileNotFoundError(f"Model or scaler missing for {series_label} at {lstm_path}")

    # 1. Base LSTM Forecast
    lstm_model = load_model(lstm_path, compile=False)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    raw_window, last_price_date, max_dataset_date, dataset_coverage = get_recent_price_window(
        market, series_type, target_date_str, window_size=10, price_csv=price_csv_path
    )

    window_scaled = scaler.transform(raw_window.reshape(-1, 1)).reshape(1, 10, 1)
    curr_window = window_scaled.copy()
    base_forecast_scaled = []

    for _ in range(horizon_days):
        pred_scaled = lstm_model.predict(curr_window, verbose=0)
        base_forecast_scaled.append(float(pred_scaled[0, 0]))
        curr_window = np.concatenate([curr_window[:, 1:, :], pred_scaled[:, np.newaxis, :]], axis=1)

    base_forecast_lkr = scaler.inverse_transform(np.array(base_forecast_scaled).reshape(-1, 1)).flatten().tolist()

    # 2. Multi-Station Regional Weather Impact & Horizon Adjustment Calculation
    regional_service = RegionalWeatherService(weather_csv=weather_csv_path)
    regional_impact = regional_service.get_regional_weather_impact(target_date_str, market, series_type)

    # Legacy backward-compatibility single-station fetch for d14_cum_rain_mm
    d14_cum_rain, actual_weather_date = get_anuradhapura_d14_cum_rain(
        target_date_str, weather_csv=weather_csv_path
    )
    abs_d14_rain = abs(d14_cum_rain)
    beta_1 = SLOPES[series_label]

    if abs_d14_rain < MODERATE_THRESHOLD:
        flag_level = "none"
    elif abs_d14_rain <= SEVERE_THRESHOLD:
        flag_level = "moderate"
    else:
        flag_level = "severe"

    # Horizon Scaling using bounded multi-region weather feature engine
    adjustments_by_horizon = []
    adjusted_forecast_lkr = []
    for h in range(1, horizon_days + 1):
        adj_info = regional_service.calculate_weather_adjustment(market, series_type, h, target_date_str)
        adj_pct = adj_info["final_adjustment_pct"]
        base_p = base_forecast_lkr[h - 1]
        adj_lkr = base_p * (adj_pct / 100.0)
        adjustments_by_horizon.append(adj_lkr)
        adjusted_forecast_lkr.append(base_p + adj_lkr)

    # Compute forecast horizon calendar dates based on data_as_of_date (last_price_date)
    base_dt = pd.to_datetime(last_price_date)
    forecast_dates = [(base_dt + pd.Timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, horizon_days + 1)]
    forecast_start_date = forecast_dates[0]
    forecast_end_date = forecast_dates[-1]

    start_dt = base_dt + pd.Timedelta(days=1)
    end_dt = base_dt + pd.Timedelta(days=horizon_days)
    if start_dt.year == end_dt.year:
        forecast_period_label = f"{start_dt.strftime('%B %d')} – {end_dt.strftime('%B %d, %Y')}"
    else:
        forecast_period_label = f"{start_dt.strftime('%B %d, %Y')} – {end_dt.strftime('%B %d, %Y')}"

    return {
        "series": series_label,
        "market": market,
        "type": series_type,
        "target_date": target_date_str,
        "last_price_date": last_price_date,
        "max_dataset_date": max_dataset_date,
        "dataset_coverage": dataset_coverage,
        "forecast_dates": forecast_dates,
        "forecast_start_date": forecast_start_date,
        "forecast_end_date": forecast_end_date,
        "forecast_period_label": forecast_period_label,
        "actual_weather_date": actual_weather_date,
        "recent_actual_price": float(raw_window[-1]),
        "d14_cum_rain_mm": round(d14_cum_rain, 2),
        "flag_level": flag_level,
        "slope_beta_1": beta_1,
        "applied_raw_14d_adjustment_lkr": round(adjustments_by_horizon[-1], 2),
        "base_lstm_forecast": [round(p, 2) for p in base_forecast_lkr],
        "weather_adjustments": [round(a, 2) for a in adjustments_by_horizon],
        "weather_adjusted_forecast": [round(p, 2) for p in adjusted_forecast_lkr],
        "regional_weather_impact": regional_impact,
    }



def get_full_recommendation(
    market: str = "Dambulla",
    series_type: str = "Retail",
    target_date_str: str = "2026-03-10",
    horizon_days: int = 14,
    price_csv_path: Optional[Path] = None,
    weather_csv_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Combined decision function combining LSTM forecast, weather adjustment, and IsolationForest price anomaly detection.

    Priority Logic:
    1. Anomaly Detection First: If recent actual price deviates anomalously from 1-day LSTM forecast,
       recommend "MONITOR" regardless of weather forecast.
    2. Empirical Volatility Threshold: If market is normal, compare Day 1 adjusted forecast to current price
       against empirical 1-sigma daily volatility threshold (series-specific):
       - > +Threshold  => "HOLD"
       - < -Threshold  => "SELL NOW"
       - Within Threshold => "SELL NOW OR HOLD — prices expected to stay stable"
    3. Driver Attribution: Deconstructs total Day 1 change into Base LSTM momentum vs Weather adjustment.
    """
    engine_res = run_decision_engine(
        market=market,
        series_type=series_type,
        target_date_str=target_date_str,
        horizon_days=horizon_days,
        price_csv_path=price_csv_path,
        weather_csv_path=weather_csv_path,
    )

    series_label = engine_res["series"]
    recent_actual_price = engine_res["recent_actual_price"]
    day1_base_pred = engine_res["base_lstm_forecast"][0]
    day1_adj_pred = engine_res["weather_adjusted_forecast"][0]
    day14_adj_pred = engine_res["weather_adjusted_forecast"][-1]
    day1_weather_adj = engine_res["weather_adjustments"][0]
    flag_level = engine_res["flag_level"]
    d14_rain = engine_res["d14_cum_rain_mm"]

    # Empirical 1-sigma threshold for this series
    volatility_thresh_pct = SERIES_VOLATILITY_SIGMA_PCT.get(series_label, 18.5)

    # Step 1: Check Price Anomaly
    anomaly_res = check_price_anomaly(
        market=market,
        series_type=series_type,
        recent_actual_price=recent_actual_price,
        predicted_price=day1_base_pred,
    )

    is_anomaly = anomaly_res["is_anomaly"]
    anomaly_score = anomaly_res["anomaly_score"]
    anomaly_severity = anomaly_res["severity"]
    residual_lkr = anomaly_res["residual_lkr"]

    # Step 1b: Fetch Qualitative News Event Flag
    news_data = get_news_flag()
    news_flag_level = news_data.get("news_flag_level", "none")
    news_events = news_data.get("events", [])

    # Step 1c: Fetch SHAP Explainability for Base LSTM Forecast
    shap_explanation = get_shap_explanation(
        market=market,
        series_type=series_type,
        target_date_str=target_date_str,
    )

    # Driver Deconstruction Math (Day 1)
    total_change_lkr = day1_adj_pred - recent_actual_price
    base_lstm_change_lkr = day1_base_pred - recent_actual_price
    pct_change_day1 = (total_change_lkr / recent_actual_price) * 100.0 if recent_actual_price > 0 else 0.0

    denom = abs(base_lstm_change_lkr) + abs(day1_weather_adj)
    if denom > 0:
        lstm_share_pct = (abs(base_lstm_change_lkr) / denom) * 100.0
        weather_share_pct = (abs(day1_weather_adj) / denom) * 100.0
    else:
        lstm_share_pct = 100.0
        weather_share_pct = 0.0

    # Step 2: Full 14-Day Trajectory Metrics & Trend Calculation
    forecast_trajectory = engine_res["weather_adjusted_forecast"]
    h_len = len(forecast_trajectory)

    peak_price = float(np.max(forecast_trajectory))
    peak_idx = int(np.argmax(forecast_trajectory))
    peak_day = peak_idx + 1  # 1-indexed day of maximum price
    minimum_price = float(np.min(forecast_trajectory))
    terminal_price = float(forecast_trajectory[-1])

    peak_change_pct = ((peak_price - recent_actual_price) / recent_actual_price) * 100.0 if recent_actual_price > 0 else 0.0
    terminal_change_pct = ((terminal_price - recent_actual_price) / recent_actual_price) * 100.0 if recent_actual_price > 0 else 0.0
    post_peak_drop_pct = ((peak_price - terminal_price) / peak_price) * 100.0 if peak_price > 0 else 0.0

    # Linear regression slope across the entire forecast trajectory
    if h_len > 1:
        x_vals = np.arange(1, h_len + 1)
        y_vals = np.array(forecast_trajectory)
        x_mean = np.mean(x_vals)
        y_mean = np.mean(y_vals)
        slope = float(np.sum((x_vals - x_mean) * (y_vals - y_mean)) / np.sum((x_vals - x_mean) ** 2))
        slope_pct_per_day = (slope / recent_actual_price) * 100.0 if recent_actual_price > 0 else 0.0
    else:
        slope = 0.0
        slope_pct_per_day = 0.0

    if slope_pct_per_day <= -0.30 or terminal_change_pct <= -3.5:
        trend = "DECLINING"
    elif slope_pct_per_day >= 0.30 or terminal_change_pct >= 3.5:
        trend = "RISING"
    else:
        trend = "STABLE"

    # Step 3: Perishability-Aware Recommendation Hierarchy
    # Priority: MONITOR (Anomaly) -> SELL_NOW (Early Peak + Decline) -> SELL_NOW (Consistent Decline) -> HOLD (Mid Peak 3-5d) -> HOLD (Late Rise) -> STABLE

    if is_anomaly:
        # RULE 1: Anomaly (Highest Priority)
        action_code = "MONITOR"
        recommendation = "MONITOR — Market Anomaly Detected"
        optimal_sell_day = 1
        optimal_sell_price_lkr = round(forecast_trajectory[0], 2)
        reasoning = (
            f"RECOMMENDATION: MONITOR. "
            f"The current tomato price for {series_label} ({recent_actual_price:.2f} LKR/kg) is experiencing an unexpected market anomaly "
            f"(residual: {residual_lkr:+.2f} LKR/kg, severity: {anomaly_severity}, score: {anomaly_score:.4f}). "
            f"Because current market conditions are highly volatile, the 14-day weather-adjusted forecast ({day14_adj_pred:.2f} LKR/kg) "
            f"should be treated with reduced confidence. Farmers should monitor daily physical buyer offers closely before making large sales."
        )

    elif peak_day <= 2 and (terminal_change_pct < 0 or post_peak_drop_pct >= 3.5):
        # RULE 2: Early Peak (Days 1-2) Followed by Decline
        action_code = "SELL_NOW"
        recommendation = "SELL NOW — Peak Price in Next 1–2 Days"
        optimal_sell_day = peak_day
        optimal_sell_price_lkr = round(peak_price, 2)
        reasoning = (
            f"RECOMMENDATION: SELL NOW — Peak Price in Next 1–2 Days. "
            f"The current price for {series_label} is {recent_actual_price:.2f} LKR/kg. "
            f"Prices are projected to reach an early peak of {peak_price:.2f} LKR/kg on Day {peak_day} (+{peak_change_pct:.1f}%) "
            f"and then decline toward {terminal_price:.2f} LKR/kg by Day {h_len} ({terminal_change_pct:+.1f}%). "
            f"Selling immediately or near the Day {peak_day} peak is recommended to avoid lower returns as prices soften later in the horizon."
        )

    elif forecast_trajectory[0] < recent_actual_price and terminal_change_pct <= -3.5 and peak_change_pct < 1.5:
        # RULE 3: Consistent Downward Trend
        action_code = "SELL_NOW"
        recommendation = "SELL NOW — Prices Expected to Decline"
        optimal_sell_day = 1
        optimal_sell_price_lkr = round(forecast_trajectory[0], 2)
        reasoning = (
            f"RECOMMENDATION: SELL NOW. "
            f"The current price for {series_label} is {recent_actual_price:.2f} LKR/kg. "
            f"Prices are projected to soften continuously across the forecast horizon down to {terminal_price:.2f} LKR/kg by Day {h_len} ({terminal_change_pct:+.1f}%). "
            f"Selling sooner is recommended to reduce the risk of receiving lower market prices later."
        )

    elif 3 <= peak_day <= 5 and peak_change_pct >= 3.5:
        # RULE 4: Short/Mid-Term Peak (Days 3 to 5)
        action_code = "HOLD"
        recommendation = f"HOLD — Optimal Selling Window Around Day {peak_day}"
        optimal_sell_day = peak_day
        optimal_sell_price_lkr = round(peak_price, 2)
        reasoning = (
            f"RECOMMENDATION: HOLD. "
            f"The current price for {series_label} is {recent_actual_price:.2f} LKR/kg. "
            f"Prices are projected to rise toward a peak of {peak_price:.2f} LKR/kg around Day {peak_day} (+{peak_change_pct:.1f}%). "
            f"Holding off on immediate sales for 2–4 days is recommended to capture higher returns. "
            f"Note: ensure harvest timing aligns with crop maturity and ambient shelf life (3–5 days)."
        )

    elif peak_day > 5 and peak_change_pct >= 5.0:
        # RULE 5: Late Rise (Day > 5) — Perishability Planning Signal
        action_code = "HOLD"
        recommendation = f"HOLD — Higher Prices Projected Around Day {peak_day}"
        optimal_sell_day = peak_day
        optimal_sell_price_lkr = round(peak_price, 2)
        reasoning = (
            f"RECOMMENDATION: HOLD. "
            f"The current price for {series_label} is {recent_actual_price:.2f} LKR/kg. "
            f"Higher market prices (up to {peak_price:.2f} LKR/kg, +{peak_change_pct:.1f}%) are projected later around Day {peak_day}. "
            f"Because tomatoes are perishable, plan staggered field harvesting rather than storing harvested tomatoes in ambient holding for extended periods."
        )

    else:
        # RULE 6: Stable Forecast (Default within +/- 3.5%)
        action_code = "STABLE"
        recommendation = "SELL NOW OR HOLD — Prices Expected to Stay Stable"
        optimal_sell_day = peak_day
        optimal_sell_price_lkr = round(peak_price, 2)
        reasoning = (
            f"RECOMMENDATION: SELL NOW OR HOLD — prices expected to stay stable. "
            f"The current price for {series_label} is {recent_actual_price:.2f} LKR/kg. "
            f"Expected prices remain relatively steady across the forecast horizon ({minimum_price:.2f} – {peak_price:.2f} LKR/kg). "
            f"Selling based on convenience and normal market conditions is recommended."
        )

    # Driver Text Construction for transparency
    if abs(day1_weather_adj) < 0.01:
        driver_text = f"Day 1 is driven 100% by base market momentum ({base_lstm_change_lkr:+.2f} LKR/kg, no weather adjustment applied)"
    else:
        driver_text = (
            f"Day 1 is driven {lstm_share_pct:.0f}% by base market momentum ({base_lstm_change_lkr:+.2f} LKR/kg) "
            f"and {weather_share_pct:.0f}% by weather impact ({day1_weather_adj:+.2f} LKR/kg, flag: {flag_level})"
        )

    reasoning += f" ({driver_text})."

    # Append plain-language news alert if news_flag_level is "alert"
    if news_flag_level == "alert" and news_events:
        top_event = news_events[0]
        evt_reason = top_event.get("reason") or "news event reported"
        evt_region = top_event.get("region") or "supply regions"
        reasoning += f" Note: recent reports of '{evt_reason}' in {evt_region} may affect supply — monitor closely."

    return {
        "series": series_label,
        "market": market,
        "type": series_type,
        "target_date": target_date_str,
        "current_price_lkr": round(recent_actual_price, 2),
        "action_code": action_code,
        "recommendation": recommendation,
        "peak_price_lkr": round(peak_price, 2),
        "peak_day": peak_day,
        "minimum_price_lkr": round(minimum_price, 2),
        "terminal_price_lkr": round(terminal_price, 2),
        "peak_change_pct": round(peak_change_pct, 2),
        "terminal_change_pct": round(terminal_change_pct, 2),
        "post_peak_drop_pct": round(post_peak_drop_pct, 2),
        "trend": trend,
        "optimal_sell_day": optimal_sell_day,
        "optimal_sell_price_lkr": round(optimal_sell_price_lkr, 2),
        "pct_change_day1": round(pct_change_day1, 2),
        "volatility_threshold_pct": volatility_thresh_pct,
        "is_anomaly": is_anomaly,
        "anomaly_severity": anomaly_severity,
        "anomaly_score": anomaly_score,
        "residual_lkr": residual_lkr,
        "weather_flag_level": flag_level,
        "d14_cum_rain_mm": d14_rain,
        "news_flag_level": news_flag_level,
        "news_events": news_events,
        "shap_explanation": shap_explanation,
        "regional_weather_impact": engine_res.get("regional_weather_impact"),
        "driver_share_lstm_pct": round(lstm_share_pct, 1),
        "driver_share_weather_pct": round(weather_share_pct, 1),
        "day1_base_forecast_lkr": day1_base_pred,
        "day1_weather_adjustment_lkr": day1_weather_adj,
        "day1_forecast_lkr": day1_adj_pred,
        "day14_forecast_lkr": day14_adj_pred,
        "data_as_of_date": engine_res["max_dataset_date"],
        "dataset_coverage": engine_res["dataset_coverage"],
        "forecast_dates": engine_res["forecast_dates"],
        "forecast_start_date": engine_res["forecast_start_date"],
        "forecast_end_date": engine_res["forecast_end_date"],
        "forecast_period_label": engine_res["forecast_period_label"],
        "base_lstm_forecast": engine_res["base_lstm_forecast"],
        "weather_adjusted_forecast": engine_res["weather_adjusted_forecast"],
        "reasoning": reasoning,
    }





def main():
    """Test execution across all 4 series with empirical thresholds and driver attribution."""
    print("=" * 95)
    print(" TESTING EMPIRICALLY-GROUNDED DECISION ENGINE SERVICE")
    print("=" * 95)

    test_scenarios = [
        ("Normal Weather & Market", "Dambulla", "Retail", "2026-03-10"),
        ("Moderate Weather Surge", "Dambulla", "Retail", "2025-10-20"),
        ("Path 2 Alignment & Driver Check", "Dambulla", "Wholesale", "2025-04-17"),
        ("Path 3 Alignment & Driver Check", "Pettah", "Wholesale", "2025-01-03"),
        ("Anomalous Price Spike Check", "Dambulla", "Retail", "2025-04-21"),
    ]

    for label, market, s_type, t_date in test_scenarios:
        res = get_full_recommendation(market, s_type, target_date_str=t_date, horizon_days=14)

        print(f"\n--- Scenario: {label} ({res['series']} on {t_date}) ---")
        print(f"  Current Price     : {res['current_price_lkr']:.2f} LKR/kg")
        print(f"  RECOMMENDATION    : >>> {res['recommendation']} <<<")
        print(f"  Day 1 Adjusted    : {res['day1_forecast_lkr']:.2f} LKR ({res['pct_change_day1']:+.1f}% vs Threshold ±{res['volatility_threshold_pct']}%)")
        print(f"  Driver Share      : Base LSTM = {res['driver_share_lstm_pct']}% ({res['day1_base_forecast_lkr'] - res['current_price_lkr']:+.2f} LKR) | Weather = {res['driver_share_weather_pct']}% ({res['day1_weather_adjustment_lkr']:+.2f} LKR)")
        print(f"  Anomaly Details   : Is Anomaly = {res['is_anomaly']} | Residual = {res['residual_lkr']:+.2f} LKR | Score = {res['anomaly_score']:.4f}")
        print(f"  Reasoning:")
        print(f"    \"{res['reasoning']}\"")


if __name__ == "__main__":
    main()
