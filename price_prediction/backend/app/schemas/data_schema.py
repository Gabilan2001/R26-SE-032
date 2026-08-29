"""Request/response schemas for price dataset update endpoint."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

SUPPORTED_MARKETS = {"Dambulla", "Pettah"}
SUPPORTED_TYPES = {"Retail", "Wholesale"}


class PriceUpdateRequest(BaseModel):
    """Input payload for updating historical price dataset."""

    market: str = Field(..., description="Market location: Dambulla or Pettah.")
    type: str = Field(..., description="Series type: Retail or Wholesale.")
    date: str = Field(..., description="Observation date (YYYY-MM-DD).")
    price: float = Field(..., gt=0, description="Price in LKR/kg (must be positive).")

    @field_validator("market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean not in SUPPORTED_MARKETS:
            raise ValueError(f"Invalid market '{v}'. Supported markets: {sorted(SUPPORTED_MARKETS)}")
        return clean

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        clean = v.strip().capitalize()
        if clean not in SUPPORTED_TYPES:
            raise ValueError(f"Invalid series type '{v}'. Supported types: {sorted(SUPPORTED_TYPES)}")
        return clean

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            parsed = date.fromisoformat(v.strip())
            return parsed.isoformat()
        except ValueError:
            raise ValueError(f"Invalid date format '{v}'. Expected YYYY-MM-DD.")


class PriceUpdateRecord(BaseModel):
    date: str
    item: str = "Tomato"
    type: str
    market: str
    price: float


class DatasetSummary(BaseModel):
    latest_date: str
    total_records: int
    series_records_count: int


class PriceUpdateResponse(BaseModel):
    status: str = "success"
    message: str
    action: str = Field(..., description="updated | inserted")
    record: PriceUpdateRecord
    dataset_summary: DatasetSummary
