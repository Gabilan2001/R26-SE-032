"""
Retrain experimental BiLSTM models and scalers on the expanded dataset (9,279 rows).
Saves artifacts in backend/ml_models/experimental/ without overwriting production models.
"""

from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import LSTM, Bidirectional, Dense, Dropout
from tensorflow.keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler

# Set seeds for reproducibility
SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
EXP_MODEL_DIR = BASE_DIR / "ml_models" / "experimental"
EXP_MODEL_DIR.mkdir(parents=True, exist_ok=True)

SERIES_LIST = [
    ("Dambulla", "Retail"),
    ("Dambulla", "Wholesale"),
    ("Pettah", "Retail"),
    ("Pettah", "Wholesale"),
]

LOOKBACK = 10

def retrain_series(market: str, series_type: str):
    file_suffix = f"{market.lower()}_{series_type.lower()}"
    print(f"\n==================================================")
    print(f" Retraining Experimental BiLSTM: {market}-{series_type}")
    print(f"==================================================")

    df = pd.read_csv(DATA_PATH)
    df.columns = [c.strip() for c in df.columns]
    sub_df = df[(df["Market"] == market) & (df["Type"] == series_type)].copy()
    sub_df["Date"] = pd.to_datetime(sub_df["Date"])
    sub_df = sub_df.sort_values("Date").reset_index(drop=True)
    
    sub_df["Price"] = pd.to_numeric(sub_df["Price"], errors="coerce")
    sub_df["Price"] = sub_df["Price"].interpolate(method="linear", limit_direction="both")
    
    total_rows = len(sub_df)
    prices_1d = sub_df["Price"].values

    X_raw, y_raw = [], []
    for i in range(LOOKBACK, len(prices_1d)):
        X_raw.append(prices_1d[i - LOOKBACK : i])
        y_raw.append(prices_1d[i])

    X_raw, y_raw = np.array(X_raw), np.array(y_raw)
    split_idx = int(len(X_raw) * 0.8)

    X_train_raw, X_test_raw = X_raw[:split_idx], X_raw[split_idx:]
    y_train_raw, y_test_raw = y_raw[:split_idx], y_raw[split_idx:]

    # New scaler fit on 1D training prices of expanded dataset
    scaler = MinMaxScaler(feature_range=(0, 1))
    train_prices_1d = prices_1d[: split_idx + LOOKBACK]
    scaler.fit(train_prices_1d.reshape(-1, 1))

    X_train_scaled = scaler.transform(X_train_raw.reshape(-1, 1)).reshape(X_train_raw.shape)
    X_test_scaled = scaler.transform(X_test_raw.reshape(-1, 1)).reshape(X_test_raw.shape)
    y_train_scaled = scaler.transform(y_train_raw.reshape(-1, 1)).flatten()
    y_test_scaled = scaler.transform(y_test_raw.reshape(-1, 1)).flatten()

    X_train_3d = np.reshape(X_train_scaled, (X_train_scaled.shape[0], X_train_scaled.shape[1], 1))
    X_test_3d = np.reshape(X_test_scaled, (X_test_scaled.shape[0], X_test_scaled.shape[1], 1))

    # Exact production BiLSTM architecture
    lstm_model = Sequential([
        Bidirectional(LSTM(units=50, return_sequences=True), input_shape=(LOOKBACK, 1)),
        Dropout(0.2),
        Bidirectional(LSTM(units=50, return_sequences=False)),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1),
    ])
    lstm_model.compile(optimizer="adam", loss="mean_squared_error")

    early_stop = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=0.0001)

    print(f"Training set size: {len(X_train_raw)} sequences (prices up to {sub_df['Date'].iloc[split_idx + LOOKBACK].strftime('%Y-%m-%d')})")
    print(f"Test set size: {len(X_test_raw)} sequences (prices up to {sub_df['Date'].iloc[-1].strftime('%Y-%m-%d')})")

    lstm_model.fit(
        X_train_3d,
        y_train_scaled,
        epochs=50,
        batch_size=32,
        validation_data=(X_test_3d, y_test_scaled),
        callbacks=[early_stop, reduce_lr],
        verbose=0,
    )

    exp_model_path = EXP_MODEL_DIR / f"lstm_{file_suffix}.h5"
    exp_scaler_path = EXP_MODEL_DIR / f"scaler_{file_suffix}.pkl"

    lstm_model.save(exp_model_path)
    with open(exp_scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    print(f"Saved experimental model to: {exp_model_path}")
    print(f"Saved experimental scaler to: {exp_scaler_path}")
    print(f"New Scaler Range: min={scaler.data_min_[0]:.2f}, max={scaler.data_max_[0]:.2f}")

if __name__ == "__main__":
    for m, t in SERIES_LIST:
        retrain_series(m, t)
    print("\nExperimental retraining complete!")
