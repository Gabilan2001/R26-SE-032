from typing import List


def normalize_prices(prices: List[float]) -> List[float]:
    """Normalize prices to a common range for feature engineering."""
    if not prices:
        return []
    minimum = min(prices)
    maximum = max(prices)
    range_value = maximum - minimum or 1.0
    return [(price - minimum) / range_value for price in prices]
