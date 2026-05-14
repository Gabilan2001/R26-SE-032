from typing import List


def prepare_time_series_features(past_prices: List[float], window_size: int) -> List[List[float]]:
    """Build time-series input windows for the LSTM model."""
    if len(past_prices) < window_size:
        raise ValueError("past_prices length must be greater than or equal to window_size")

    windows = []
    for index in range(len(past_prices) - window_size + 1):
        window = past_prices[index : index + window_size]
        windows.append(window)

    return windows
