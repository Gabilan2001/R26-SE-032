"""
SHAP Explainability Service for LSTM Price Forecasts.
Calculates SHAP values for the Day-1 LSTM prediction, attributing feature importance
to each input timestep in the 10-day lookback window.
"""

from __future__ import annotations

import logging
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import shap
from tensorflow.keras.models import load_model

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "ml_models"
DATA_PATH = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"

# Global In-Memory Caches
# 1. Background Datasets per series (cached across server lifecycle)
_BG_CACHE: Dict[str, Tuple[np.ndarray, Any, Any]] = {}

# 2. SHAP Result Cache per (series_label, target_date) with 1-hour TTL
_SHAP_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


def _get_series_artifacts(market: str, series_type: str) -> Tuple[np.ndarray, Any, Any]:
    """
    Load Keras LSTM model, MinMaxScaler, and background dataset (50 historical 10-day windows).
    Caches model & background data in memory to avoid redundant IO.
    """
    series_label = f"{market}-{series_type}"
    if series_label in _BG_CACHE:
        return _BG_CACHE[series_label]

    file_suffix = f"{market.lower()}_{series_type.lower()}"
    lstm_path = MODEL_DIR / f"lstm_{file_suffix}.h5"
    scaler_path = MODEL_DIR / f"scaler_{file_suffix}.pkl"

    if not lstm_path.exists() or not scaler_path.exists():
        raise FileNotFoundError(f"Missing LSTM model or scaler for series {series_label}")

    model = load_model(lstm_path, compile=False)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    # Load dataset to extract historical background windows
    df = pd.read_csv(DATA_PATH)
    sub_df = df[(df["Market"] == market) & (df["Type"] == series_type)].copy()
    sub_df["Date"] = pd.to_datetime(sub_df["Date"])
    sub_df = sub_df.sort_values("Date").reset_index(drop=True)
    prices = sub_df["Price"].interpolate(method="linear", limit_direction="both").values

    window_size = 10
    X_raw = []
    for i in range(window_size, len(prices)):
        X_raw.append(prices[i - window_size : i])
    X_raw = np.array(X_raw)

    split_idx = int(len(X_raw) * 0.8)
    X_train_raw = X_raw[:split_idx]

    # Transform 2D training windows
    X_train_scaled = scaler.transform(X_train_raw.reshape(-1, 1)).reshape(X_train_raw.shape)

    # Sample 50 representative background windows
    np.random.seed(42)
    sample_count = min(50, len(X_train_scaled))
    bg_indices = np.random.choice(len(X_train_scaled), size=sample_count, replace=False)
    background_2d = X_train_scaled[bg_indices] # shape: (50, 10)

    _BG_CACHE[series_label] = (background_2d, model, scaler)
    return background_2d, model, scaler


def get_shap_explanation(
    market: str = "Dambulla",
    series_type: str = "Retail",
    target_date_str: str = "2026-03-10",
    lookback_prices_raw: Optional[List[float]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Compute SHAP value attributions for Day-1 LSTM prediction.
    Attributes forecast output to each of the 10 lookback timesteps (t-10..t-1).
    Returns ranked timesteps, contributions in LKR, and a plain-language summary.
    """
    series_label = f"{market}-{series_type}"
    cache_key = f"{series_label}_{target_date_str}"
    now_ts = time.time()

    # 1. Check SHAP result cache
    if cache_key in _SHAP_CACHE:
        cached_time, cached_res = _SHAP_CACHE[cache_key]
        if (now_ts - cached_time) < CACHE_TTL_SECONDS:
            return cached_res

    try:
        t0 = time.time()
        background_2d, model, scaler = _get_series_artifacts(market, series_type)

        # 2. Extract recent 10-day lookback raw prices if not provided
        if lookback_prices_raw is None or len(lookback_prices_raw) < 10:
            df = pd.read_csv(DATA_PATH)
            sub_df = df[(df["Market"] == market) & (df["Type"] == series_type)].copy()
            sub_df["Date"] = pd.to_datetime(sub_df["Date"])
            sub_df = sub_df.sort_values("Date").reset_index(drop=True)

            target_dt = pd.to_datetime(target_date_str)
            sub = sub_df[sub_df["Date"] <= target_dt]
            if len(sub) < 10:
                return None
            lookback_prices_raw = sub["Price"].tail(10).tolist()

        lookback_arr = np.array(lookback_prices_raw[-10:])
        live_scaled_2d = scaler.transform(lookback_arr.reshape(-1, 1)).reshape(1, 10)

        # 3. Model Predictor Wrapper for 2D inputs
        def predict_2d(x_2d: np.ndarray) -> np.ndarray:
            x_3d = np.reshape(x_2d, (x_2d.shape[0], 10, 1))
            preds_scaled = model.predict(x_3d, verbose=0)
            return scaler.inverse_transform(preds_scaled).flatten()

        # 4. Compute SHAP values via KernelExplainer
        explainer = shap.KernelExplainer(predict_2d, background_2d)
        shap_vals = explainer.shap_values(live_scaled_2d, nsamples=80)

        sv = shap_vals[0] if isinstance(shap_vals, list) else shap_vals.flatten()

        # 5. Format & Rank Timestep Contributions
        timesteps_output: List[Dict[str, Any]] = []
        for idx in range(10):
            lag_days = 10 - idx
            raw_p = float(lookback_arr[idx])
            s_val = float(sv[idx])
            timesteps_output.append({
                "timestep_label": f"{lag_days} day{'s' if lag_days > 1 else ''} ago (t-{lag_days})",
                "lag_days": lag_days,
                "observed_price_lkr": round(raw_p, 2),
                "shap_contribution_lkr": round(s_val, 2),
                "direction": "positive" if s_val >= 0 else "negative",
            })

        timesteps_ranked = sorted(timesteps_output, key=lambda x: abs(x["shap_contribution_lkr"]), reverse=True)
        top_item = timesteps_ranked[0]

        summary_sentence = (
            f"Forecast is driven mainly by price movement from {top_item['timestep_label']} "
            f"({top_item['observed_price_lkr']:.2f} LKR/kg), contributing {top_item['shap_contribution_lkr']:+.2f} LKR "
            f"to the Day-1 prediction."
        )

        elapsed_sec = time.time() - t0

        result = {
            "summary_sentence": summary_sentence,
            "top_contributor": top_item,
            "ranked_timesteps": timesteps_ranked,
            "computation_time_seconds": round(elapsed_sec, 3),
        }

        _SHAP_CACHE[cache_key] = (now_ts, result)
        return result

    except Exception as exc:
        logger.warning("SHAP explanation calculation failed for %s on %s: %s", series_label, target_date_str, exc)
        return None
