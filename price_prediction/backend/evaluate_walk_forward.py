"""
Standalone Walk-Forward Evaluation Script for Tomato Price Forecasting Models.

Performs a rigorous 5-fold expanding-window time-series evaluation across 4 market series,
6 forecasting models, and 4 forecast horizons (1, 3, 7, 14 days).

DO NOT MODIFY PRODUCTION CODE, MODELS, OR ENDPOINTS.
Saves results to:
- ml_models/walk_forward_evaluation_results.json
- ml_models/walk_forward_evaluation_results.csv
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pickle
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb

import pmdarima as pm
from statsmodels.tsa.arima.model import ARIMA

import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import GRU, LSTM, Bidirectional, Dense, Dropout
from tensorflow.keras.models import Sequential

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("walk_forward_eval")

# Set random seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
OUTPUT_DIR = BASE_DIR / "ml_models"

LOOKBACK = 10
HORIZONS = [1, 3, 7, 14]
MAX_HORIZON = max(HORIZONS)

SERIES_LIST = [
    ("Dambulla", "Retail"),
    ("Dambulla", "Wholesale"),
    ("Pettah", "Retail"),
    ("Pettah", "Wholesale"),
]

MODEL_NAMES = [
    "Naive Baseline",
    "ARIMA",
    "Bidirectional LSTM",
    "Bidirectional GRU",
    "Random Forest",
    "XGBoost",
    "Direct Multi-Output Bi-LSTM",
]


def load_and_preprocess_series(market: str, series_type: str) -> pd.DataFrame:
    """Load CSV dataset, filter by Market/Type, sort by Date, and linear-interpolate NaNs."""
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df.columns = [col.strip() for col in df.columns]

    sub = df[(df["Market"] == market) & (df["Type"] == series_type)].copy()
    if sub.empty:
        raise ValueError(f"No rows found for Market={market}, Type={series_type}")

    sub["Date"] = pd.to_datetime(sub["Date"])
    sub = sub.sort_values("Date").reset_index(drop=True)

    sub["Price"] = pd.to_numeric(sub["Price"], errors="coerce")
    sub["Price"] = sub["Price"].interpolate(method="linear", limit_direction="both")

    if sub["Price"].isna().sum() > 0:
        raise ValueError(f"NaNs remain in {market}-{series_type} after interpolation!")

    return sub


def calculate_metrics(y_true_lkr: np.ndarray, y_pred_lkr: np.ndarray, y_ref_lkr: np.ndarray) -> Dict[str, float]:
    """
    Calculate Regression Metrics (MAE, RMSE, MAPE) and Directional Classification Metrics.

    Directional Logic:
    - Actual Direction: UP if P(t+h) > P(t), else NOT-UP (0)
    - Predicted Direction: UP if P_hat(t+h) > P(t), else NOT-UP (0)
    """
    # 1. Regression Metrics
    mae = float(np.mean(np.abs(y_true_lkr - y_pred_lkr)))
    rmse = float(np.sqrt(np.mean((y_true_lkr - y_pred_lkr) ** 2)))

    # Prevent division by zero in MAPE
    denom = np.where(np.abs(y_true_lkr) < 1e-5, 1e-5, np.abs(y_true_lkr))
    mape = float(np.mean(np.abs((y_true_lkr - y_pred_lkr) / denom)) * 100.0)

    # 2. Binary Directional Classification (UP vs NOT-UP)
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


def train_lstm_model(X_train_3d: np.ndarray, y_train_scaled: np.ndarray) -> Sequential:
    """Build and train production Bidirectional LSTM architecture."""
    model = Sequential([
        Bidirectional(LSTM(units=50, return_sequences=True), input_shape=(LOOKBACK, 1)),
        Dropout(0.2),
        Bidirectional(LSTM(units=50, return_sequences=False)),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1),
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")
    early_stop = EarlyStopping(monitor="loss", patience=8, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor="loss", factor=0.5, patience=4, min_lr=0.0001)

    model.fit(
        X_train_3d,
        y_train_scaled,
        epochs=35,
        batch_size=32,
        callbacks=[early_stop, reduce_lr],
        verbose=0,
    )
    return model


def train_gru_model(X_train_3d: np.ndarray, y_train_scaled: np.ndarray) -> Sequential:
    """Build and train production Bidirectional GRU architecture."""
    model = Sequential([
        Bidirectional(GRU(units=50, return_sequences=True), input_shape=(LOOKBACK, 1)),
        Dropout(0.2),
        Bidirectional(GRU(units=50, return_sequences=False)),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1),
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")
    early_stop = EarlyStopping(monitor="loss", patience=8, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor="loss", factor=0.5, patience=4, min_lr=0.0001)

    model.fit(
        X_train_3d,
        y_train_scaled,
        epochs=35,
        batch_size=32,
        callbacks=[early_stop, reduce_lr],
        verbose=0,
    )
    return model


def train_lstm_direct_mimo_model(X_train_3d: np.ndarray, Y_train_14d_scaled: np.ndarray) -> Sequential:
    """Build and train Direct Multi-Output (Dense-14) Bidirectional LSTM architecture."""
    model = Sequential([
        Bidirectional(LSTM(units=50, return_sequences=True), input_shape=(LOOKBACK, 1)),
        Dropout(0.2),
        Bidirectional(LSTM(units=50, return_sequences=False)),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=MAX_HORIZON),
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")
    early_stop = EarlyStopping(monitor="loss", patience=8, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor="loss", factor=0.5, patience=4, min_lr=0.0001)

    model.fit(
        X_train_3d,
        Y_train_14d_scaled,
        epochs=35,
        batch_size=32,
        callbacks=[early_stop, reduce_lr],
        verbose=0,
    )
    return model


def evaluate_fold(
    df_series: pd.DataFrame,
    fold_num: int,
    train_pct: float,
    test_pct: float,
    market: str,
    series_type: str,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """Execute evaluation for one expanding fold across all 6 models."""
    prices = df_series["Price"].values
    dates = df_series["Date"].values
    total_len = len(prices)

    # 1. Calculate Chronological Fold Cutoffs
    train_end_raw_idx = int(total_len * train_pct)
    test_end_raw_idx = min(int(total_len * (train_pct + test_pct)), total_len)

    # 2. Build 10-day sliding window samples
    X_all_raw, y_all_raw, origin_dates, origin_indices = [], [], [], []
    for i in range(LOOKBACK, total_len):
        X_all_raw.append(prices[i - LOOKBACK : i])
        y_all_raw.append(prices[i])
        origin_dates.append(dates[i - 1])  # Date of P(t)
        origin_indices.append(i - 1)

    X_all_raw = np.array(X_all_raw)
    y_all_raw = np.array(y_all_raw)

    # Fold train/test sample index bounds
    train_sample_mask = np.array([idx < train_end_raw_idx for idx in origin_indices])
    test_sample_mask = np.array([(idx >= train_end_raw_idx) and (idx < test_end_raw_idx) for idx in origin_indices])

    X_train_raw = X_all_raw[train_sample_mask]
    y_train_raw = y_all_raw[train_sample_mask]

    X_test_raw_full = X_all_raw[test_sample_mask]

    # Critical Assertion 1: Chronological Order & Non-Overlap
    train_last_date = dates[train_end_raw_idx - 1]
    test_first_date = dates[train_end_raw_idx]
    assert pd.to_datetime(train_last_date) < pd.to_datetime(test_first_date), (
        f"Data leakage detected! Train last date ({train_last_date}) >= Test first date ({test_first_date})"
    )

    # Filter test origins to only those where full MAX_HORIZON (14 days) targets exist
    valid_test_eval_count = len(X_test_raw_full) - (MAX_HORIZON - 1)
    if valid_test_eval_count <= 0:
        logger.warning("Fold %d has insufficient test samples for 14-day horizon.", fold_num)
        return []

    X_test_eval_raw = X_test_raw_full[:valid_test_eval_count]  # shape: (valid_test_count, 10)
    eval_origin_indices = [idx for idx, mask in zip(origin_indices, test_sample_mask) if mask][:valid_test_eval_count]

    # Target Reference Prices P(t) at forecast origins
    today_prices = X_test_eval_raw[:, -1]

    # Ground Truth Target Matrices P(t+h) for h in [1, 3, 7, 14]
    actuals_by_h = {}
    for h in HORIZONS:
        actuals_by_h[h] = np.array([prices[orig_idx + h] for orig_idx in eval_origin_indices])

    # Critical Assertion 2: Scaling Scoping (fit MinMaxScaler ONLY on training slice)
    train_prices_1d = prices[:train_end_raw_idx]
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(train_prices_1d.reshape(-1, 1))

    X_train_scaled = scaler.transform(X_train_raw.reshape(-1, 1)).reshape(X_train_raw.shape)
    X_train_3d = np.reshape(X_train_scaled, (X_train_scaled.shape[0], X_train_scaled.shape[1], 1))
    y_train_scaled = scaler.transform(y_train_raw.reshape(-1, 1)).flatten()

    fold_results = []
    series_label = f"{market}-{series_type}"

    train_start_str = pd.to_datetime(dates[0]).strftime("%Y-%m-%d")
    train_end_str = pd.to_datetime(dates[train_end_raw_idx - 1]).strftime("%Y-%m-%d")
    test_start_str = pd.to_datetime(dates[train_end_raw_idx]).strftime("%Y-%m-%d")
    test_end_str = pd.to_datetime(dates[test_end_raw_idx - 1]).strftime("%Y-%m-%d")

    logger.info(
        "--- Fold %d [%s] Train: %s to %s (%d) | Test: %s to %s (%d origins) ---",
        fold_num,
        series_label,
        train_start_str,
        train_end_str,
        len(X_train_raw),
        test_start_str,
        test_end_str,
        valid_test_eval_count,
    )

    # =========================================================================
    # 1. Naive Baseline (P_hat(t+h) = P(t))
    # =========================================================================
    for h in HORIZONS:
        y_true = actuals_by_h[h]
        y_pred = today_prices  # Baseline uses P(t) for all horizons
        m = calculate_metrics(y_true, y_pred, today_prices)
        fold_results.append({
            "Model": "Naive Baseline",
            "Series": series_label,
            "Market": market,
            "Type": series_type,
            "Fold": fold_num,
            "Horizon": f"{h}-day",
            "Horizon_Days": h,
            "Train_Start": train_start_str,
            "Train_End": train_end_str,
            "Test_Start": test_start_str,
            "Test_End": test_end_str,
            "Sample_Count": valid_test_eval_count,
            **m,
        })

    # =========================================================================
    # 2. ARIMA (Statsmodels state-space forecast)
    # =========================================================================
    try:
        auto_fit = pm.auto_arima(
            train_prices_1d,
            seasonal=False,
            stepwise=True,
            suppress_warnings=True,
            error_action="ignore",
            max_p=4,
            max_q=4,
        )
        order = auto_fit.order
    except Exception:
        order = (2, 1, 2)

    sm_arima_base = ARIMA(train_prices_1d, order=order).fit()
    test_prices_1d = prices[train_end_raw_idx : test_end_raw_idx]

    arima_preds_matrix = np.zeros((valid_test_eval_count, MAX_HORIZON))
    for i in range(valid_test_eval_count):
        if i == 0:
            sub_m = sm_arima_base
        else:
            sub_m = sm_arima_base.append(test_prices_1d[:i], refit=False)
        fc = sub_m.forecast(steps=MAX_HORIZON)
        arima_preds_matrix[i, :] = fc

    for h in HORIZONS:
        y_true = actuals_by_h[h]
        y_pred = arima_preds_matrix[:, h - 1]
        m = calculate_metrics(y_true, y_pred, today_prices)
        fold_results.append({
            "Model": "ARIMA",
            "Series": series_label,
            "Market": market,
            "Type": series_type,
            "Fold": fold_num,
            "Horizon": f"{h}-day",
            "Horizon_Days": h,
            "Train_Start": train_start_str,
            "Train_End": train_end_str,
            "Test_Start": test_start_str,
            "Test_End": test_end_str,
            "Sample_Count": valid_test_eval_count,
            **m,
        })

    # =========================================================================
    # 3. Bidirectional LSTM (Recursive Autoregressive Prediction)
    # =========================================================================
    lstm_model = train_lstm_model(X_train_3d, y_train_scaled)
    curr_scaled_lstm = scaler.transform(X_test_eval_raw.reshape(-1, 1)).reshape(valid_test_eval_count, LOOKBACK, 1)
    lstm_preds_matrix = np.zeros((valid_test_eval_count, MAX_HORIZON))

    for step in range(MAX_HORIZON):
        p_scaled = lstm_model.predict(curr_scaled_lstm, verbose=0)
        p_real = scaler.inverse_transform(p_scaled).flatten()
        lstm_preds_matrix[:, step] = p_real
        # Critical Assertion 3: Self-generated recursive prediction (no future target leakage)
        curr_scaled_lstm = np.concatenate([curr_scaled_lstm[:, 1:, :], p_scaled[:, np.newaxis, :]], axis=1)

    for h in HORIZONS:
        y_true = actuals_by_h[h]
        y_pred = lstm_preds_matrix[:, h - 1]
        m = calculate_metrics(y_true, y_pred, today_prices)
        fold_results.append({
            "Model": "Bidirectional LSTM",
            "Series": series_label,
            "Market": market,
            "Type": series_type,
            "Fold": fold_num,
            "Horizon": f"{h}-day",
            "Horizon_Days": h,
            "Train_Start": train_start_str,
            "Train_End": train_end_str,
            "Test_Start": test_start_str,
            "Test_End": test_end_str,
            "Sample_Count": valid_test_eval_count,
            **m,
        })

    # =========================================================================
    # 4. Bidirectional GRU (Recursive Autoregressive Prediction)
    # =========================================================================
    gru_model = train_gru_model(X_train_3d, y_train_scaled)
    curr_scaled_gru = scaler.transform(X_test_eval_raw.reshape(-1, 1)).reshape(valid_test_eval_count, LOOKBACK, 1)
    gru_preds_matrix = np.zeros((valid_test_eval_count, MAX_HORIZON))

    for step in range(MAX_HORIZON):
        p_scaled = gru_model.predict(curr_scaled_gru, verbose=0)
        p_real = scaler.inverse_transform(p_scaled).flatten()
        gru_preds_matrix[:, step] = p_real
        curr_scaled_gru = np.concatenate([curr_scaled_gru[:, 1:, :], p_scaled[:, np.newaxis, :]], axis=1)

    for h in HORIZONS:
        y_true = actuals_by_h[h]
        y_pred = gru_preds_matrix[:, h - 1]
        m = calculate_metrics(y_true, y_pred, today_prices)
        fold_results.append({
            "Model": "Bidirectional GRU",
            "Series": series_label,
            "Market": market,
            "Type": series_type,
            "Fold": fold_num,
            "Horizon": f"{h}-day",
            "Horizon_Days": h,
            "Train_Start": train_start_str,
            "Train_End": train_end_str,
            "Test_Start": test_start_str,
            "Test_End": test_end_str,
            "Sample_Count": valid_test_eval_count,
            **m,
        })

    # =========================================================================
    # 5. Random Forest (Recursive Autoregressive Prediction on Raw LKR)
    # =========================================================================
    rf_model = RandomForestRegressor(n_estimators=100, random_state=SEED)
    rf_model.fit(X_train_raw, y_train_raw)

    curr_flat_rf = X_test_eval_raw.copy()
    rf_preds_matrix = np.zeros((valid_test_eval_count, MAX_HORIZON))
    for step in range(MAX_HORIZON):
        p_real = rf_model.predict(curr_flat_rf)
        rf_preds_matrix[:, step] = p_real
        curr_flat_rf = np.hstack([curr_flat_rf[:, 1:], p_real.reshape(-1, 1)])

    for h in HORIZONS:
        y_true = actuals_by_h[h]
        y_pred = rf_preds_matrix[:, h - 1]
        m = calculate_metrics(y_true, y_pred, today_prices)
        fold_results.append({
            "Model": "Random Forest",
            "Series": series_label,
            "Market": market,
            "Type": series_type,
            "Fold": fold_num,
            "Horizon": f"{h}-day",
            "Horizon_Days": h,
            "Train_Start": train_start_str,
            "Train_End": train_end_str,
            "Test_Start": test_start_str,
            "Test_End": test_end_str,
            "Sample_Count": valid_test_eval_count,
            **m,
        })

    # =========================================================================
    # 6. XGBoost (Recursive Autoregressive Prediction on Raw LKR)
    # =========================================================================
    xgb_model = xgb.XGBRegressor(n_estimators=100, random_state=SEED)
    xgb_model.fit(X_train_raw, y_train_raw)

    curr_flat_xgb = X_test_eval_raw.copy()
    xgb_preds_matrix = np.zeros((valid_test_eval_count, MAX_HORIZON))
    for step in range(MAX_HORIZON):
        p_real = xgb_model.predict(curr_flat_xgb)
        xgb_preds_matrix[:, step] = p_real
        curr_flat_xgb = np.hstack([curr_flat_xgb[:, 1:], p_real.reshape(-1, 1)])

    for h in HORIZONS:
        y_true = actuals_by_h[h]
        y_pred = xgb_preds_matrix[:, h - 1]
        m = calculate_metrics(y_true, y_pred, today_prices)
        fold_results.append({
            "Model": "XGBoost",
            "Series": series_label,
            "Market": market,
            "Type": series_type,
            "Fold": fold_num,
            "Horizon": f"{h}-day",
            "Horizon_Days": h,
            "Train_Start": train_start_str,
            "Train_End": train_end_str,
            "Test_Start": test_start_str,
            "Test_End": test_end_str,
            "Sample_Count": valid_test_eval_count,
            **m,
        })

    # =========================================================================
    # 7. Direct Multi-Output Bidirectional LSTM (Dense-14 One-Shot Prediction)
    # =========================================================================
    # Construct 14-day training targets strictly within training slice (no future leakage)
    X_train_mimo_raw = []
    Y_train_mimo_raw = []
    for orig_idx in range(LOOKBACK - 1, train_end_raw_idx - MAX_HORIZON):
        X_train_mimo_raw.append(prices[orig_idx - LOOKBACK + 1 : orig_idx + 1])
        Y_train_mimo_raw.append(prices[orig_idx + 1 : orig_idx + MAX_HORIZON + 1])

    X_train_mimo_raw = np.array(X_train_mimo_raw)
    Y_train_mimo_raw = np.array(Y_train_mimo_raw)

    if len(X_train_mimo_raw) > 0:
        X_train_mimo_scaled = scaler.transform(X_train_mimo_raw.reshape(-1, 1)).reshape(len(X_train_mimo_raw), LOOKBACK, 1)
        Y_train_mimo_scaled = scaler.transform(Y_train_mimo_raw.reshape(-1, 1)).reshape(len(Y_train_mimo_raw), MAX_HORIZON)

        mimo_model = train_lstm_direct_mimo_model(X_train_mimo_scaled, Y_train_mimo_scaled)
        curr_scaled_mimo = scaler.transform(X_test_eval_raw.reshape(-1, 1)).reshape(valid_test_eval_count, LOOKBACK, 1)

        # Single one-shot direct prediction for all 14 horizons
        p_scaled_mimo = mimo_model.predict(curr_scaled_mimo, verbose=0)
        p_real_mimo = scaler.inverse_transform(p_scaled_mimo.reshape(-1, 1)).reshape(valid_test_eval_count, MAX_HORIZON)

        for h in HORIZONS:
            y_true = actuals_by_h[h]
            y_pred = p_real_mimo[:, h - 1]
            m = calculate_metrics(y_true, y_pred, today_prices)
            fold_results.append({
                "Model": "Direct Multi-Output Bi-LSTM",
                "Series": series_label,
                "Market": market,
                "Type": series_type,
                "Fold": fold_num,
                "Horizon": f"{h}-day",
                "Horizon_Days": h,
                "Train_Start": train_start_str,
                "Train_End": train_end_str,
                "Test_Start": test_start_str,
                "Test_End": test_end_str,
                "Sample_Count": valid_test_eval_count,
                **m,
            })

    return fold_results


def run_walk_forward_experiment(dry_run: bool = False) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Execute 5-fold expanding-window evaluation across 4 market series."""
    folds_config = [
        (1, 0.50, 0.10),
        (2, 0.60, 0.10),
        (3, 0.70, 0.10),
        (4, 0.80, 0.10),
        (5, 0.90, 0.10),
    ]

    if dry_run:
        logger.info("Executing DRY-RUN validation test (1 market series, 1 fold)...")
        target_series = [SERIES_LIST[0]]
        target_folds = [folds_config[0]]
    else:
        logger.info("Starting FULL Walk-Forward Evaluation (4 series, 5 folds, 6 models, 4 horizons)...")
        target_series = SERIES_LIST
        target_folds = folds_config

    all_records = []
    t_start = time.time()

    for market, series_type in target_series:
        df_series = load_and_preprocess_series(market, series_type)
        for fold_num, train_pct, test_pct in target_folds:
            records = evaluate_fold(
                df_series, fold_num, train_pct, test_pct, market, series_type, dry_run=dry_run
            )
            all_records.extend(records)

    elapsed_sec = time.time() - t_start
    results_df = pd.DataFrame(all_records)

    # Compute Aggregated Metrics (Mean ± Std Dev) across Folds per Model, Market & Horizon
    metrics_cols = ["MAE", "RMSE", "MAPE", "Accuracy", "Precision", "Recall", "F1"]
    group_cols = ["Model", "Series", "Horizon"]
    agg_df = results_df.groupby(group_cols)[metrics_cols].agg(["mean", "std"]).reset_index()

    # Structure JSON Output
    json_summary = {
        "metadata": {
            "title": "5-Fold Expanding Window Walk-Forward Evaluation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "random_seed": SEED,
            "lookback_days": LOOKBACK,
            "horizons_evaluated": HORIZONS,
            "folds_count": len(folds_config),
            "dry_run": dry_run,
            "elapsed_seconds": round(elapsed_sec, 2),
        },
        "records_count": len(results_df),
        "detailed_results": all_records,
    }

    if not dry_run:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        csv_path_mimo = OUTPUT_DIR / "walk_forward_evaluation_with_mimo.csv"
        json_path_mimo = OUTPUT_DIR / "walk_forward_evaluation_with_mimo.json"
        csv_path_std = OUTPUT_DIR / "walk_forward_evaluation_results.csv"
        json_path_std = OUTPUT_DIR / "walk_forward_evaluation_results.json"

        results_df.to_csv(csv_path_mimo, index=False)
        results_df.to_csv(csv_path_std, index=False)
        with open(json_path_mimo, "w", encoding="utf-8") as f:
            json.dump(json_summary, f, indent=2)
        with open(json_path_std, "w", encoding="utf-8") as f:
            json.dump(json_summary, f, indent=2)

        logger.info("Saved CSV results to %s and %s", csv_path_mimo, csv_path_std)
        logger.info("Saved JSON summary to %s and %s", json_path_mimo, json_path_std)

    return results_df, json_summary


def main():
    parser = argparse.ArgumentParser(description="Walk-Forward Evaluation Script")
    parser.add_argument("--dry-run", action="store_true", help="Run small dry-run test (1 market, 1 fold)")
    args = parser.parse_args()

    results_df, json_summary = run_walk_forward_experiment(dry_run=args.dry_run)

    print("\n" + "=" * 80)
    print(" WALK-FORWARD EVALUATION CONSOLIDATED SUMMARY")
    print("=" * 80)
    if not results_df.empty:
        agg = results_df.groupby(["Horizon", "Model"])[["MAE", "RMSE", "MAPE", "Accuracy", "F1"]].mean().reset_index()
        print(agg.to_string(index=False))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
