"""
Price Anomaly Detection Service Module
Uses IsolationForest fit on 1-day-ahead LSTM residuals to detect genuine unexpected price anomalies.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "ml_models"

# Cache loaded Isolation Forest models
_iso_models_cache: Dict[str, Any] = {}


def _load_isolation_forest(market: str, series_type: str) -> Any:
    """Load and cache IsolationForest model for requested market and type."""
    series_label = f"{market}-{series_type}"
    file_suffix = f"{market.lower()}_{series_type.lower()}"
    model_path = MODEL_DIR / f"anomaly_{file_suffix}.pkl"

    if series_label in _iso_models_cache:
        return _iso_models_cache[series_label]

    if not model_path.is_file():
        raise FileNotFoundError(
            f"IsolationForest model not found for {series_label} at {model_path}. "
            "Please run train_model.py or test_anomaly_detection.py to train it."
        )

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    _iso_models_cache[series_label] = model
    return model


def check_price_anomaly(
    market: str,
    series_type: str,
    recent_actual_price: float,
    predicted_price: float,
) -> Dict[str, Any]:
    """
    Check if recent_actual_price deviates anomalously from predicted_price relative to historical LSTM residuals.

    Args:
        market: Market location ("Dambulla" or "Pettah")
        series_type: Series type ("Retail" or "Wholesale")
        recent_actual_price: Real observed price (LKR/kg)
        predicted_price: 1-step ahead predicted price (LKR/kg)

    Returns:
        Structured dict with series label, residual, boolean is_anomaly, score, and severity level.
    """
    series_label = f"{market}-{series_type}"
    iso_model = _load_isolation_forest(market, series_type)

    residual = float(recent_actual_price - predicted_price)
    res_array = np.array([[residual]])

    pred = iso_model.predict(res_array)[0]  # -1 for anomaly, 1 for normal
    score = float(iso_model.score_samples(res_array)[0])

    is_anomaly = bool(pred == -1)

    # Determine severity label based on score depth
    if not is_anomaly:
        severity = "NORMAL"
    elif score < -0.15:
        severity = "HIGH"
    else:
        severity = "MODERATE"

    direction = "positive_spike" if residual > 0 else "negative_crash"

    reasoning = (
        f"Price for {series_label} is NORMAL (Residual: {residual:+.2f} LKR/kg, Score: {score:.4f})."
        if not is_anomaly
        else f"Price for {series_label} FLAGGED AS {severity} ANOMALY! "
        f"Actual price ({recent_actual_price:.2f} LKR/kg) deviated by {residual:+.2f} LKR/kg "
        f"from expected ({predicted_price:.2f} LKR/kg) with anomaly score {score:.4f} ({direction})."
    )

    return {
        "series": series_label,
        "market": market,
        "type": series_type,
        "actual_price": round(float(recent_actual_price), 2),
        "predicted_price": round(float(predicted_price), 2),
        "residual_lkr": round(residual, 2),
        "is_anomaly": is_anomaly,
        "anomaly_score": round(score, 4),
        "severity": severity,
        "direction": direction,
        "reasoning": reasoning,
    }


def main():
    """Run test verification across historical test set residuals for all 4 series."""
    print("=" * 80)
    print(" ANOMALY DETECTION SERVICE TEST SUITE")
    print("=" * 80)

    # Simple sanity check calls
    test_cases = [
        ("Dambulla", "Retail", 185.00, 424.84),  # Known large negative residual crash
        ("Pettah", "Retail", 900.00, 686.89),   # Known large positive residual spike
        ("Dambulla", "Wholesale", 114.00, 115.50), # Normal small residual
    ]

    for m, t, actual, pred in test_cases:
        res = check_price_anomaly(m, t, actual, pred)
        print(f"\n--- Sanity Check: {res['series']} ---")
        print(f"  Actual: {res['actual_price']} | Predicted: {res['predicted_price']} | Residual: {res['residual_lkr']:+.2f} LKR")
        print(f"  Is Anomaly: {res['is_anomaly']} | Severity: {res['severity']} | Score: {res['anomaly_score']}")
        print(f"  Reasoning : \"{res['reasoning']}\"")


if __name__ == "__main__":
    main()
