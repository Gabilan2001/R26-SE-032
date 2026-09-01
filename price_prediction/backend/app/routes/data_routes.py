# NOTE: Adding or updating price rows in tomato_prices_vegetablesSriLanka.csv
# updates the dataset for predictions, but does NOT automatically retrain the
# LSTM or IsolationForest models (train_model.py).

from __future__ import annotations

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
import pandas as pd

from app.schemas.data_schema import (
    DatasetSummary,
    PriceUpdateRecord,
    PriceUpdateRequest,
    PriceUpdateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"


def _update_csv_dataset(req: PriceUpdateRequest) -> PriceUpdateResponse:
    """Read CSV, update or insert requested row, write back sorted by Date."""
    if not DATASET_PATH.is_file():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Price dataset file not found at {DATASET_PATH}",
        )

    df = pd.read_csv(DATASET_PATH)
    df.columns = [col.strip().replace('"', '') for col in df.columns]

    # Standardize column types
    df["Date"] = df["Date"].astype(str).str.strip()
    df["Market"] = df["Market"].astype(str).str.strip()
    df["Type"] = df["Type"].astype(str).str.strip()
    df["Item"] = df["Item"].astype(str).str.strip() if "Item" in df.columns else "Tomato"

    # Match existing row
    match_mask = (
        (df["Date"] == req.date)
        & (df["Market"].str.casefold() == req.market.casefold())
        & (df["Type"].str.casefold() == req.type.casefold())
    )

    action = "updated" if match_mask.any() else "inserted"

    if action == "updated":
        df.loc[match_mask, "Price"] = req.price
        df.loc[match_mask, "Market"] = req.market
        df.loc[match_mask, "Type"] = req.type
        df.loc[match_mask, "Item"] = "Tomato"
    else:
        new_row = pd.DataFrame([{
            "Date": req.date,
            "Item": "Tomato",
            "Type": req.type,
            "Market": req.market,
            "Price": req.price,
        }])
        df = pd.concat([df, new_row], ignore_index=True)

    # Sort dataset chronologically
    df["dt_sort"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.sort_values(by=["dt_sort", "Market", "Type"]).drop(columns=["dt_sort"]).reset_index(drop=True)

    # Write back matching original header format: "Date","Item","Type","Market","Price"
    df.to_csv(
        DATASET_PATH,
        index=False,
        columns=["Date", "Item", "Type", "Market", "Price"],
    )

    # Clear cached DataFrames in dataset_price_service if imported
    try:
        import app.services.dataset_price_service as dps
        dps._df_cache = None
        dps._cache_mtime = None
    except Exception:
        pass

    latest_date = str(df["Date"].max())
    total_records = len(df)
    series_sub = df[(df["Market"].str.casefold() == req.market.casefold()) & (df["Type"].str.casefold() == req.type.casefold())]
    series_records_count = len(series_sub)

    msg = f"Price record for {req.market}-{req.type} on {req.date} successfully {action}."

    return PriceUpdateResponse(
        status="success",
        message=msg,
        action=action,
        record=PriceUpdateRecord(
            date=req.date,
            item="Tomato",
            type=req.type,
            market=req.market,
            price=float(req.price),
        ),
        dataset_summary=DatasetSummary(
            latest_date=latest_date,
            total_records=total_records,
            series_records_count=series_records_count,
        ),
    )


@router.post(
    "/update",
    response_model=PriceUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update or insert historical tomato price observation",
)
def update_price_dataset(request: PriceUpdateRequest):
    """
    Manually or automatically update/append a tomato price entry in the dataset.

    Validates market, series type, date format, and positive numeric price.
    If a record exists for the date/market/type combination, it is updated;
    otherwise, a new row is appended.
    """
    try:
        return _update_csv_dataset(request)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Failed to update price dataset: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dataset: {exc}",
        ) from exc


@router.post(
    "/sync-daily",
    status_code=status.HTTP_200_OK,
    summary="Trigger daily CBSL and market price bulletin synchronization",
)
def sync_daily_prices():
    """
    Trigger the automated CBSL daily price ingestion pipeline.
    Scans for new bulletins, resolves gaps, deduplicates entries, and updates the dataset.
    """
    try:
        from app.services.scheduler_service import trigger_cbsl_ingestion_sync
        result = trigger_cbsl_ingestion_sync()
        return result
    except Exception as exc:
        logger.error("Failed to sync daily prices: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync daily prices: {exc}",
        ) from exc
