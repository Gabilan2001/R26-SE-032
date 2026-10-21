"""
Compare Old BiLSTM vs Retrained BiLSTM vs Naive Baseline on the 80/20 Chronological Test Set of the Expanded CBSL Dataset.
Calculates MAE, RMSE, MAPE for 1-day, 3-day, 7-day, and 14-day horizons across all 4 market series.
Also outputs percentage error changes and explicit answers to research questions.
"""

from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
BACKUP_DIR = BASE_DIR / "ml_models" / "backups" / "backup_20260829_101550"
EXP_DIR = BASE_DIR / "ml_models" / "experimental"

SERIES_LIST = [
    ("Dambulla", "Retail"),
    ("Dambulla", "Wholesale"),
    ("Pettah", "Retail"),
    ("Pettah", "Wholesale"),
]

LOOKBACK = 10
HORIZONS = [1, 3, 7, 14]
MAX_HORIZON = max(HORIZONS)

results = []

def evaluate_models_for_series(market: str, series_type: str):
    file_suffix = f"{market.lower()}_{series_type.lower()}"
    series_label = f"{market}-{series_type}"
    print(f"Evaluating 80/20 test split for {series_label}...", flush=True)

    df = pd.read_csv(DATA_PATH)
    df.columns = [c.strip() for c in df.columns]
    sub = df[(df["Market"] == market) & (df["Type"] == series_type)].copy()
    sub["Date"] = pd.to_datetime(sub["Date"])
    sub = sub.sort_values("Date").reset_index(drop=True)
    sub["Price"] = pd.to_numeric(sub["Price"], errors="coerce")
    sub["Price"] = sub["Price"].interpolate(method="linear", limit_direction="both")

    prices = sub["Price"].values
    total_len = len(prices)

    # 10-day lookback sequences
    X_raw, y_raw, ref_prices = [], [], []
    for i in range(LOOKBACK, total_len):
        X_raw.append(prices[i - LOOKBACK : i])
        y_raw.append(prices[i])
        ref_prices.append(prices[i - 1]) # P(t)

    X_raw = np.array(X_raw)
    y_raw = np.array(y_raw)
    ref_prices = np.array(ref_prices)

    split_idx = int(len(X_raw) * 0.8)

    # Test set sequences
    X_test_raw_full = X_raw[split_idx:]
    ref_test_full = ref_prices[split_idx:]

    valid_test_count = len(X_test_raw_full) - (MAX_HORIZON - 1)
    X_test_eval_raw = X_test_raw_full[:valid_test_count]
    ref_test_eval = ref_test_full[:valid_test_count]

    # Actual targets for each horizon
    actuals = {}
    for h in HORIZONS:
        actuals[h] = np.array([prices[split_idx + LOOKBACK + i + (h - 1)] for i in range(valid_test_count)])

    # Load Old Model & Scaler
    old_model = load_model(BACKUP_DIR / f"lstm_{file_suffix}.h5", compile=False)
    with open(BACKUP_DIR / f"scaler_{file_suffix}.pkl", "rb") as f:
        old_scaler = pickle.load(f)

    # Load Retrained Model & Scaler
    new_model = load_model(EXP_DIR / f"lstm_{file_suffix}.h5", compile=False)
    with open(EXP_DIR / f"scaler_{file_suffix}.pkl", "rb") as f:
        new_scaler = pickle.load(f)

    # Helper for recursive forecasting
    def get_recursive_preds(model, scaler):
        curr_windows_scaled = scaler.transform(X_test_eval_raw.reshape(-1, 1)).reshape(valid_test_count, LOOKBACK, 1)
        preds_matrix = np.zeros((valid_test_count, MAX_HORIZON))
        for step in range(MAX_HORIZON):
            preds_scaled = model.predict(curr_windows_scaled, verbose=0)
            preds_real = scaler.inverse_transform(preds_scaled).flatten()
            preds_matrix[:, step] = preds_real
            curr_windows_scaled = np.concatenate([curr_windows_scaled[:, 1:, :], preds_scaled[:, np.newaxis, :]], axis=1)
        return preds_matrix

    old_preds_matrix = get_recursive_preds(old_model, old_scaler)
    new_preds_matrix = get_recursive_preds(new_model, new_scaler)

    for h in HORIZONS:
        y_true = actuals[h]
        
        # Naive: P_hat(t+h) = P(t)
        naive_pred = ref_test_eval
        old_pred = old_preds_matrix[:, h - 1]
        new_pred = new_preds_matrix[:, h - 1]

        def calc_metrics(yt, yp):
            mae = float(np.mean(np.abs(yt - yp)))
            rmse = float(np.sqrt(np.mean((yt - yp) ** 2)))
            denom = np.where(np.abs(yt) < 1e-5, 1e-5, np.abs(yt))
            mape = float(np.mean(np.abs((yt - yp) / denom)) * 100.0)
            return mae, rmse, mape

        n_mae, n_rmse, n_mape = calc_metrics(y_true, naive_pred)
        o_mae, o_rmse, o_mape = calc_metrics(y_true, old_pred)
        r_mae, r_rmse, r_mape = calc_metrics(y_true, new_pred)

        results.append({
            "Series": series_label,
            "Horizon": f"{h}-day",
            "Naive_MAE": n_mae, "Naive_RMSE": n_rmse, "Naive_MAPE": n_mape,
            "Old_MAE": o_mae, "Old_RMSE": o_rmse, "Old_MAPE": o_mape,
            "New_MAE": r_mae, "New_RMSE": r_rmse, "New_MAPE": r_mape,
            "MAE_Diff_%": ((o_mae - r_mae) / o_mae) * 100.0,
            "RMSE_Diff_%": ((o_rmse - r_rmse) / o_rmse) * 100.0,
            "MAPE_Diff_%": ((o_mape - r_mape) / o_mape) * 100.0,
            "New_vs_Naive_MAE_%": ((n_mae - r_mae) / n_mae) * 100.0,
        })

if __name__ == "__main__":
    for m, t in SERIES_LIST:
        evaluate_models_for_series(m, t)

    res_df = pd.DataFrame(results)
    res_df.to_csv(BASE_DIR / "ml_models" / "experimental_comparison_8020.csv", index=False)
    print("\n=== 80/20 TEST SET EVALUATION COMPLETE ===")
    print(res_df.to_string())
