import numpy as np
from typing import List

def prepare_time_series_features(past_prices: List[float], window_size: int) -> np.ndarray:
    """Build time-series input windows for the LSTM model."""
    if len(past_prices) < window_size:
        raise ValueError("past_prices length must be greater than or equal to window_size")

    # We only take the most recent window for a single prediction
    window = past_prices[-window_size:]
    
    # Reshape to [samples, time steps, features] -> [1, window_size, 1]
    return np.array(window).reshape((1, window_size, 1))
