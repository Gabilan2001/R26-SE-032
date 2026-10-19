"""
Experimental Script: Direct Multi-Horizon Bidirectional LSTM.

Trains and evaluates a direct multi-output BiLSTM variant:
  Input: 10-day lookback window (samples, 10, 1)
  Architecture: Bidirectional(LSTM(50)) -> Dropout(0.2) -> Bidirectional(LSTM(50)) -> Dropout(0.2) -> Dense(25) -> Dense(14)
  Output: Direct 14-day price forecast vector (samples, 14)

Compares performance against the production Recursive 1-Step BiLSTM across:
  - 4 market series (Dambulla-Retail, Dambulla-Wholesale, Pettah-Retail, Pettah-Wholesale)
  - 4 horizons (1-day, 3-day, 7-day, 14-day)
  - Metrics: MAE, RMSE, MAPE, Directional Accuracy, Directional F1 score.

SAFETY: Does NOT modify or overwrite production model files in ml_models/.
Saves all experimental artifacts to ml_models/experimental/.
"""

from __future__ import annotations

import json
import logging
import os
import pickle
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import LSTM, Bidirectional, Dense, Dropout
from tensorflow.keras.models import Sequential, load_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("direct_multihorizon")

# Set random seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
PROD_MODEL_DIR = BASE_DIR / "ml_models"
EXP_MODEL_DIR = BASE_DIR / "ml_models" / "experimental"
EXP_MODEL_DIR.mkdir(parents=True, exist_ok=True)

LOOKBACK = 10
HORIZON_DAYS = 14
HORIZONS_TO_EVAL = [1, 3, 7, 14]

SERIES_LIST = [
    ("Dambulla", "Retail"),
    ("Dambulla", "Wholesale"),
    ("Pettah", "Retail"),
    ("Pettah", "Wholesale"),
]


def load_and_preprocess_data(market: str, series_type: str) -> pd.DataFrame:
    """Load dataset, filter series, sort chronologically, and interpolate missing values."""
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df.columns = [c.strip() for c in df.columns]

    sub = df[(df["Market"] == market) & (df["Type"] == series_type)].copy()
    if sub.empty:
        raise ValueError(f"No records found for {market}-{series_type}")

    sub["Date"] = pd.to_datetime(sub["Date"])
    sub = sub.sort_values("Date").reset_index(drop=True)
    sub["Price"] = pd.to_numeric(sub["Price"], errors="coerce")
    sub["Price"] = sub["Price"].interpolate(method="linear", limit_direction="both")

    return sub


def calculate_metrics(y_true_lkr: np.ndarray, y_pred_lkr: np.ndarray, y_ref_lkr: np.ndarray) -> Dict[str, float]:
    """Calculate MAE, RMSE, MAPE, Directional Accuracy, Precision, Recall, and F1."""
    mae = float(np.mean(np.abs(y_true_lkr - y_pred_lkr)))
    rmse = float(np.sqrt(np.mean((y_true_lkr - y_pred_lkr) ** 2)))

    denom = np.where(np.abs(y_true_lkr) < 1e-5, 1e-5, np.abs(y_true_lkr))
    mape = float(np.mean(np.abs((y_true_lkr - y_pred_lkr) / denom)) * 100.0)

    # Directional Classification (UP vs NOT-UP vs reference price P(t))
    d_actual = (y_true_lkr > y_ref_lkr).astype(int)
    d_pred = (y_pred_lkr > y_ref_lkr).astype(int)

    acc = float(accuracy_score(d_actual, d_pred) * 100.0)
    prec = float(precision_score(d_actual, d_pred, zero_division=0) * 100.0)
    rec = float(recall_score(d_actual, d_pred, zero_division=0) * 100.0)
    f1 = float(f1_score(d_actual, d_pred, zero_division=0) * 100.0)

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": mape,
        "Accuracy": acc,
        "Precision": prec,
        "Recall": rec,
        "F1": f1,
    }


def build_direct_multihorizon_model(input_shape: Tuple[int, int], output_dim: int = HORIZON_DAYS) -> Sequential:
    """
    Build Direct Multi-Horizon BiLSTM Model.
    Uses identical base as train_model.py: Bidirectional(LSTM(50)) x2 + Dropout(0.2) x2 + Dense(25)
    with a Dense(14) output head for direct single-pass vector forecasting.
    """
    model = Sequential([
        Bidirectional(LSTM(units=50, return_sequences=True), input_shape=input_shape),
        Dropout(0.2),
        Bidirectional(LSTM(units=50, return_sequences=False)),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=output_dim),  # Direct 14-output head
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def run_experiment_for_series(market: str, series_type: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    series_label = f"{market}-{series_type}"
    file_suffix = f"{market.lower()}_{series_type.lower()}"
    logger.info("=" * 70)
    logger.info(" Running Direct Multi-Horizon Experiment for: %s", series_label)
    logger.info("=" * 70)

    df_series = load_and_preprocess_data(market, series_type)
    prices = df_series["Price"].values
    dates = df_series["Date"].values
    total_len = len(prices)

    # 1. Build 10-day lookback sequences with 14-day multi-output target vectors
    X_raw, Y_raw, ref_prices, origin_dates = [], [], [], []
    for i in range(total_len - LOOKBACK - HORIZON_DAYS + 1):
        x_window = prices[i : i + LOOKBACK]
        y_targets = prices[i + LOOKBACK : i + LOOKBACK + HORIZON_DAYS]
        ref_p = x_window[-1]  # P(t) price at forecast origin

        X_raw.append(x_window)
        Y_raw.append(y_targets)
        ref_prices.append(ref_p)
        origin_dates.append(dates[i + LOOKBACK - 1])

    X_raw = np.array(X_raw)      # Shape: (N, 10)
    Y_raw = np.array(Y_raw)      # Shape: (N, 14)
    ref_prices = np.array(ref_prices)

    # 2. Chronological 80/20 train/test split
    split_idx = int(len(X_raw) * 0.8)
    X_train_raw, X_test_raw = X_raw[:split_idx], X_raw[split_idx:]
    Y_train_raw, Y_test_raw = Y_raw[:split_idx], Y_raw[split_idx:]
    ref_test = ref_prices[split_idx:]

    train_last_date = origin_dates[split_idx - 1]
    test_first_date = origin_dates[split_idx]
    logger.info("Train slice: %d samples (ending %s)", len(X_train_raw), pd.to_datetime(train_last_date).strftime("%Y-%m-%d"))
    logger.info("Test slice:  %d samples (starting %s)", len(X_test_raw), pd.to_datetime(test_first_date).strftime("%Y-%m-%d"))

    # 3. Fit MinMaxScaler strictly on 1D training slice
    scaler = MinMaxScaler(feature_range=(0, 1))
    train_prices_1d = prices[: split_idx + LOOKBACK]
    scaler.fit(train_prices_1d.reshape(-1, 1))

    X_train_scaled = scaler.transform(X_train_raw.reshape(-1, 1)).reshape(X_train_raw.shape)
    X_test_scaled = scaler.transform(X_test_raw.reshape(-1, 1)).reshape(X_test_raw.shape)

    Y_train_scaled = scaler.transform(Y_train_raw.reshape(-1, 1)).reshape(Y_train_raw.shape)
    Y_test_scaled = scaler.transform(Y_test_raw.reshape(-1, 1)).reshape(Y_test_raw.shape)

    X_train_3d = np.reshape(X_train_scaled, (X_train_scaled.shape[0], X_train_scaled.shape[1], 1))
    X_test_3d = np.reshape(X_test_scaled, (X_test_scaled.shape[0], X_test_scaled.shape[1], 1))

    # 4. Build and train Direct Multi-Horizon BiLSTM
    direct_model = build_direct_multihorizon_model(input_shape=(LOOKBACK, 1), output_dim=HORIZON_DAYS)
    early_stop = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=0.0001)

    logger.info("Training Direct Multi-Horizon BiLSTM model...")
    t0 = time.time()
    history = direct_model.fit(
        X_train_3d,
        Y_train_scaled,
        epochs=50,
        batch_size=32,
        validation_data=(X_test_3d, Y_test_scaled),
        callbacks=[early_stop, reduce_lr],
        verbose=0,
    )
    train_duration = time.time() - t0
    logger.info("Training complete in %.2f seconds (stopped at epoch %d)", train_duration, len(history.history["loss"]))

    # Save experimental direct model and scaler
    exp_model_path = EXP_MODEL_DIR / f"direct_lstm_{file_suffix}.h5"
    exp_scaler_path = EXP_MODEL_DIR / f"direct_scaler_{file_suffix}.pkl"
    direct_model.save(exp_model_path)
    with open(exp_scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    logger.info("Saved experimental model to: %s", exp_model_path.name)

    # 5. Direct Model Multi-Step Forecast on Test Set
    direct_pred_scaled = direct_model.predict(X_test_3d, verbose=0)  # Shape: (N_test, 14)
    direct_pred_lkr = scaler.inverse_transform(direct_pred_scaled.reshape(-1, 1)).reshape(direct_pred_scaled.shape)

    # 6. Baseline 1: Production Recursive BiLSTM Forecast on the Exact Same Test Set
    prod_lstm_path = PROD_MODEL_DIR / f"lstm_{file_suffix}.h5"
    prod_scaler_path = PROD_MODEL_DIR / f"scaler_{file_suffix}.pkl"

    if prod_lstm_path.is_file() and prod_scaler_path.is_file():
        prod_model = load_model(prod_lstm_path, compile=False)
        with open(prod_scaler_path, "rb") as f:
            prod_scaler = pickle.load(f)

        # Recursive roll-forward simulation on test set
        curr_windows_scaled = prod_scaler.transform(X_test_raw.reshape(-1, 1)).reshape(len(X_test_raw), LOOKBACK, 1)
        recursive_preds_lkr = np.zeros((len(X_test_raw), HORIZON_DAYS))

        for step in range(HORIZON_DAYS):
            p_scaled = prod_model.predict(curr_windows_scaled, verbose=0)
            p_real = prod_scaler.inverse_transform(p_scaled).flatten()
            recursive_preds_lkr[:, step] = p_real
            curr_windows_scaled = np.concatenate([curr_windows_scaled[:, 1:, :], p_scaled[:, np.newaxis, :]], axis=1)
    else:
        logger.warning("Production recursive model not found at %s; skipping direct comparison", prod_lstm_path)
        recursive_preds_lkr = None

    # 7. Baseline 2: Naive Persistence Baseline (P_hat(t+h) = P(t))
    naive_preds_lkr = np.repeat(ref_test[:, np.newaxis], HORIZON_DAYS, axis=1)

    # 8. Compute and Compare Horizon Metrics (1, 3, 7, 14 days)
    series_eval_records = []
    for h in HORIZONS_TO_EVAL:
        h_idx = h - 1
        y_true = Y_raw[split_idx:, h_idx]

        # Evaluate Direct Multi-Horizon BiLSTM
        dir_metrics = calculate_metrics(y_true, direct_pred_lkr[:, h_idx], ref_test)

        # Evaluate Recursive BiLSTM
        if recursive_preds_lkr is not None:
            rec_metrics = calculate_metrics(y_true, recursive_preds_lkr[:, h_idx], ref_test)
            mae_diff_lkr = dir_metrics["MAE"] - rec_metrics["MAE"]
            mae_diff_pct = (mae_diff_lkr / rec_metrics["MAE"]) * 100.0
        else:
            rec_metrics = {"MAE": np.nan, "RMSE": np.nan, "MAPE": np.nan, "Accuracy": np.nan, "F1": np.nan}
            mae_diff_lkr = np.nan
            mae_diff_pct = np.nan

        # Evaluate Naive Baseline
        naive_metrics = calculate_metrics(y_true, naive_preds_lkr[:, h_idx], ref_test)

        record = {
            "Series": series_label,
            "Market": market,
            "Type": series_type,
            "Horizon": f"{h}-day",
            "Horizon_Days": h,
            "Test_Samples": len(y_true),
            # Direct Model
            "Direct_MAE": dir_metrics["MAE"],
            "Direct_RMSE": dir_metrics["RMSE"],
            "Direct_MAPE": dir_metrics["MAPE"],
            "Direct_Accuracy": dir_metrics["Accuracy"],
            "Direct_F1": dir_metrics["F1"],
            # Recursive Model
            "Recursive_MAE": rec_metrics["MAE"],
            "Recursive_RMSE": rec_metrics["RMSE"],
            "Recursive_MAPE": rec_metrics["MAPE"],
            "Recursive_Accuracy": rec_metrics["Accuracy"],
            "Recursive_F1": rec_metrics["F1"],
            # Naive Baseline
            "Naive_MAE": naive_metrics["MAE"],
            "Naive_RMSE": naive_metrics["RMSE"],
            "Naive_MAPE": naive_metrics["MAPE"],
            # Comparison Metrics
            "MAE_Diff_LKR (Direct - Rec)": mae_diff_lkr,
            "MAE_Diff_Pct (%)": mae_diff_pct,
            "Direct_Wins": bool(dir_metrics["MAE"] < rec_metrics["MAE"]),
        }
        series_eval_records.append(record)

    return series_eval_records, {"market": market, "type": series_type, "train_duration": train_duration}


def main():
    print("\n" + "=" * 90)
    print(" DIRECT MULTI-HORIZON BiLSTM EXPERIMENT vs PRODUCTION RECURSIVE BiLSTM")
    print("=" * 90 + "\n")

    all_records = []
    series_metadata = []

    for market, series_type in SERIES_LIST:
        records, meta = run_experiment_for_series(market, series_type)
        all_records.extend(records)
        series_metadata.append(meta)

    results_df = pd.DataFrame(all_records)

    # Save evaluation summary to CSV & JSON in ml_models/experimental/
    csv_output_path = EXP_MODEL_DIR / "direct_multihorizon_evaluation_results.csv"
    json_output_path = EXP_MODEL_DIR / "direct_multihorizon_evaluation_results.json"

    results_df.to_csv(csv_output_path, index=False)

    json_payload = {
        "metadata": {
            "title": "Direct Multi-Horizon BiLSTM vs Recursive BiLSTM Evaluation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lookback_days": LOOKBACK,
            "forecast_horizon_days": HORIZON_DAYS,
            "architecture": "Bidirectional(LSTM(50)) x2 + Dropout(0.2) x2 + Dense(25) + Dense(14)",
            "series_evaluated": [f"{m}-{t}" for m, t in SERIES_LIST],
        },
        "records": all_records,
    }
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)

    logger.info("Saved CSV results to: %s", csv_output_path)
    logger.info("Saved JSON results to: %s", json_output_path)

    # =========================================================================
    # Print Comprehensive Comparison Tables
    # =========================================================================
    print("\n" + "=" * 105)
    print(" DETAILED COMPARISON TABLE: DIRECT MULTI-HORIZON BiLSTM vs RECURSIVE BiLSTM")
    print("=" * 105)

    display_cols = [
        "Series",
        "Horizon",
        "Direct_MAE",
        "Recursive_MAE",
        "MAE_Diff_LKR (Direct - Rec)",
        "MAE_Diff_Pct (%)",
        "Direct_RMSE",
        "Recursive_RMSE",
        "Direct_MAPE",
        "Recursive_MAPE",
        "Direct_F1",
        "Recursive_F1",
    ]

    formatted_df = results_df[display_cols].copy()
    formatted_df["Direct_MAE"] = formatted_df["Direct_MAE"].map(lambda x: f"{x:.2f}")
    formatted_df["Recursive_MAE"] = formatted_df["Recursive_MAE"].map(lambda x: f"{x:.2f}")
    formatted_df["MAE_Diff_LKR (Direct - Rec)"] = formatted_df["MAE_Diff_LKR (Direct - Rec)"].map(lambda x: f"{x:+.2f}")
    formatted_df["MAE_Diff_Pct (%)"] = formatted_df["MAE_Diff_Pct (%)"].map(lambda x: f"{x:+.2f}%")
    formatted_df["Direct_RMSE"] = formatted_df["Direct_RMSE"].map(lambda x: f"{x:.2f}")
    formatted_df["Recursive_RMSE"] = formatted_df["Recursive_RMSE"].map(lambda x: f"{x:.2f}")
    formatted_df["Direct_MAPE"] = formatted_df["Direct_MAPE"].map(lambda x: f"{x:.2f}%")
    formatted_df["Recursive_MAPE"] = formatted_df["Recursive_MAPE"].map(lambda x: f"{x:.2f}%")
    formatted_df["Direct_F1"] = formatted_df["Direct_F1"].map(lambda x: f"{x:.1f}%")
    formatted_df["Recursive_F1"] = formatted_df["Recursive_F1"].map(lambda x: f"{x:.1f}%")

    print(formatted_df.to_string(index=False))
    print("=" * 105)

    # Consolidated Overall Average by Horizon
    print("\n" + "=" * 80)
    print(" OVERALL CONSOLIDATED AVERAGE ACROSS ALL 4 SERIES BY HORIZON")
    print("=" * 80)
    overall_avg = results_df.groupby("Horizon")[
        ["Direct_MAE", "Recursive_MAE", "Direct_RMSE", "Recursive_RMSE", "Direct_MAPE", "Recursive_MAPE", "Direct_Accuracy", "Recursive_Accuracy", "Direct_F1", "Recursive_F1"]
    ].mean().reindex(["1-day", "3-day", "7-day", "14-day"]).reset_index()

    overall_avg["MAE_Diff_LKR"] = overall_avg["Direct_MAE"] - overall_avg["Recursive_MAE"]
    overall_avg["MAE_Diff_Pct"] = (overall_avg["MAE_Diff_LKR"] / overall_avg["Recursive_MAE"]) * 100.0

    print(
        overall_avg[
            ["Horizon", "Direct_MAE", "Recursive_MAE", "MAE_Diff_LKR", "MAE_Diff_Pct", "Direct_MAPE", "Recursive_MAPE", "Direct_F1", "Recursive_F1"]
        ].to_string(index=False)
    )
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
