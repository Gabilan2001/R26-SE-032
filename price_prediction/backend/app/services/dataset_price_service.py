"""
Load recent price windows from the training CSV for automatic LSTM input.

The saved MinMaxScaler was fit on the same series produced in train_model.py:
tomato rows if any exist, else all vegetable rows; then **national** daily mean
by Date (average across regions). We repeat that so scaled inputs match training.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
PRIMARY_DATA_PATH = BASE_DIR / "datasets" / "sri_lanka_crop_prices.csv"
FALLBACK_DATA_PATH = BASE_DIR / "datasets" / "Vegetables_fruit_prices_with_climate_130000_2020_to_2025.csv"
DEFAULT_DATA_PATH = PRIMARY_DATA_PATH if PRIMARY_DATA_PATH.is_file() else FALLBACK_DATA_PATH

_df_cache: Optional[pd.DataFrame] = None
_cache_path: Optional[Path] = None
_cache_mtime: Optional[float] = None


def _read_prices_dataframe(csv_path: Path) -> pd.DataFrame:
    """Read CSV with appropriate encoding and date column resolution."""
    df = pd.read_csv(csv_path, encoding="latin1")
    df.columns = [col.strip() for col in df.columns]
    date_col = "date" if "date" in df.columns else ("Date" if "Date" in df.columns else df.columns[0])
    df["Date"] = pd.to_datetime(df[date_col])
    return df


def get_cached_dataframe(csv_path: Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Load the dataset once per file change (mtime) to avoid re-reading 100k+ rows every request."""
    global _df_cache, _cache_path, _cache_mtime
    if not csv_path.is_file():
        raise FileNotFoundError(f"Price dataset not found at {csv_path}")
    mtime = csv_path.stat().st_mtime
    if _df_cache is not None and _cache_path == csv_path and _cache_mtime == mtime:
        return _df_cache
    logger.info("Loading price dataset from %s", csv_path)
    _df_cache = _read_prices_dataframe(csv_path)
    _cache_path = csv_path
    _cache_mtime = mtime
    return _df_cache


def _national_daily_series(df: pd.DataFrame) -> pd.Series:
    """Same filtering and aggregation as train_model.py."""
    if "productname" in df.columns:
        df_tomato = df[df["productname"].astype(str).str.contains("Tomato", case=False, na=False)].copy()
        if not df_tomato.empty:
            if "retailpricedambulla" in df_tomato.columns:
                price_col = "retailpricedambulla"
            elif "retailpricepettah" in df_tomato.columns:
                price_col = "retailpricepettah"
            elif "farmprice" in df_tomato.columns:
                price_col = "farmprice"
            else:
                price_col = df_tomato.select_dtypes(include=["number"]).columns[0]
            daily = df_tomato.groupby("Date", as_index=True)[price_col].mean().sort_index()
            return daily

    comm_cols = [c for c in df.columns if "vegitable_Commodity" in c or "commodity" in c.lower()]
    price_cols = [c for c in df.columns if "vegitable_Price" in c or "price" in c.lower()]
    
    if comm_cols:
        df_tomato = df[df[comm_cols[0]].astype(str).str.contains("Tomato", case=False, na=False)]
    else:
        df_tomato = pd.DataFrame()

    if df_tomato.empty:
        df_tomato = df

    price_col = price_cols[0] if price_cols else df.columns[-1]
    daily = df_tomato.groupby("Date", as_index=True)[price_col].mean().sort_index()
    return daily


def get_recent_prices_from_dataset(
    window_size: int,
    csv_path: Optional[Path] = None,
) -> Tuple[List[float], str]:
    """
    Return the last `window_size` national daily average vegetable prices (LKR/kg).

    Matches train_model.py so the LSTM + scaler see the same kind of input they
    were trained on. `location` does not change this series (weather/news still
    use location separately).

    Returns:
        past_prices (oldest → newest), human-readable source label.
    """
    path = csv_path or DEFAULT_DATA_PATH
    df = get_cached_dataframe(path)
    daily = _national_daily_series(df)
    if len(daily) < window_size:
        raise ValueError(
            f"Dataset has only {len(daily)} days after aggregation; need at least {window_size} for the model."
        )
    tail = daily.iloc[-window_size:]
    prices = [float(x) for x in tail.tolist()]
    label = (
        f"CSV {path.name}: national daily mean (tomato filter if present), "
        f"last {window_size} days ending {tail.index[-1].date().isoformat()}"
    )
    return prices, label
