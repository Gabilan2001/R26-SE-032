"""
Phase 14: Backtest Weather Adjustment Script.
Performs a chronological out-of-sample backtest comparing:
Model A: Price-only BiLSTM forecast baseline
Model B: BiLSTM forecast + Regional Weather Adjustment
Across horizons 1, 3, 7, and 14 days.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pickle
import sys
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_absolute_error, mean_squared_error

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.regional_weather_service import RegionalWeatherService

PRICE_CSV = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
MODEL_DIR = BASE_DIR / "ml_models"

def run_backtest():
    print("==================================================================================")
    print(" PHASE 14: HISTORICAL OUT-OF-SAMPLE BACKTEST OF WEATHER ADJUSTMENT")
    print("==================================================================================\n")

    weather_service = RegionalWeatherService()
    df_p = pd.read_csv(PRICE_CSV)
    df_p.columns = [c.strip() for c in df_p.columns]
    df_tom = df_p[df_p["Item"] == "Tomato"].copy()
    df_tom["Date"] = pd.to_datetime(df_tom["Date"])
    df_tom["Price"] = pd.to_numeric(df_tom["Price"], errors="coerce")

    series_list = [("Dambulla", "Wholesale"), ("Pettah", "Wholesale")]
    horizons = [1, 3, 7, 14]

    results = []

    for m, t in series_list:
        file_suffix = f"{m.lower()}_{t.lower()}"
        lstm_path = MODEL_DIR / f"lstm_{file_suffix}.h5"
        scaler_path = MODEL_DIR / f"scaler_{file_suffix}.pkl"

        if not lstm_path.exists() or not scaler_path.exists():
            print(f"Skipping {m}-{t}: model/scaler missing")
            continue

        lstm_model = load_model(lstm_path, compile=False)
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)

        sub = df_tom[(df_tom["Market"] == m) & (df_tom["Type"] == t)].sort_values("Date").reset_index(drop=True)
        sub["Price"] = sub["Price"].interpolate(method="linear", limit_direction="both")

        # Test set: Last 300 days of data (e.g. 2025-2026 cutoff)
        test_start_idx = len(sub) - 300

        for h in horizons:
            preds_base = []
            preds_weath = []
            actuals = []

            for i in range(test_start_idx, len(sub) - h):
                window_raw = sub.iloc[i-10:i]["Price"].values
                target_actual = sub.iloc[i + h - 1]["Price"]
                target_date_str = sub.iloc[i - 1]["Date"].strftime("%Y-%m-%d")

                # Base LSTM multi-step forecast
                win_scaled = scaler.transform(window_raw.reshape(-1, 1)).reshape(1, 10, 1)
                curr_win = win_scaled.copy()
                step_preds = []

                for _ in range(h):
                    p_sc = lstm_model.predict(curr_win, verbose=0)
                    step_preds.append(float(p_sc[0, 0]))
                    curr_win = np.concatenate([curr_win[:, 1:, :], p_sc[:, np.newaxis, :]], axis=1)

                forecast_lkr = scaler.inverse_transform(np.array(step_preds).reshape(-1, 1)).flatten()
                base_h_pred = forecast_lkr[-1]

                # Regional weather adjustment
                adj_info = weather_service.calculate_weather_adjustment(m, t, h, target_date_str)
                adj_pct = adj_info["final_adjustment_pct"]
                weath_h_pred = base_h_pred * (1.0 + adj_pct / 100.0)

                preds_base.append(base_h_pred)
                preds_weath.append(weath_h_pred)
                actuals.append(target_actual)

            mae_base = mean_absolute_error(actuals, preds_base)
            mae_weath = mean_absolute_error(actuals, preds_weath)
            rmse_base = np.sqrt(mean_squared_error(actuals, preds_base))
            rmse_weath = np.sqrt(mean_squared_error(actuals, preds_weath))
            pct_imp = ((mae_base - mae_weath) / mae_base) * 100.0

            results.append({
                "Series": f"{m}-{t}",
                "Horizon": f"{h}d",
                "Base_MAE": round(mae_base, 2),
                "Weather_MAE": round(mae_weath, 2),
                "MAE_Diff_LKR": round(mae_base - mae_weath, 2),
                "Pct_Imp (%)": round(pct_imp, 2),
                "Base_RMSE": round(rmse_base, 2),
                "Weather_RMSE": round(rmse_weath, 2),
                "Evaluated_Days": len(actuals)
            })

    df_res = pd.DataFrame(results)
    print(df_res.to_string(index=False))
    print("\n")

if __name__ == "__main__":
    run_backtest()
