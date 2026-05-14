import pickle
from pathlib import Path

from tensorflow.keras.models import load_model

MODEL_FILE = Path(__file__).resolve().parents[2] / "ml_models" / "lstm_price_predictor.h5"
SCALER_FILE = Path(__file__).resolve().parents[2] / "ml_models" / "scaler.pkl"

def load_price_model():
    """Load the TensorFlow/Keras LSTM model for tomato price forecasting."""
    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"LSTM model file not found at {MODEL_FILE}. Place the trained model in ml_models/."
        )
    return load_model(MODEL_FILE)

def load_scaler():
    """Load the MinMaxScaler for inverse scaling predictions."""
    if not SCALER_FILE.exists():
        raise FileNotFoundError(
            f"Scaler file not found at {SCALER_FILE}. Place the trained scaler in ml_models/."
        )
    with open(SCALER_FILE, "rb") as f:
        return pickle.load(f)
