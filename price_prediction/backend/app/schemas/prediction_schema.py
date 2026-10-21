"""Request/response models for the prediction API (Decision Engine + Weather + Anomaly Detection)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator
from zoneinfo import ZoneInfo

TZ_COLOMBO = ZoneInfo("Asia/Colombo")


class FarmerRecommendation(BaseModel):
    """Structured selling advice returned with each prediction."""

    action: str = Field(..., description="MONITOR | HOLD | SELL NOW | SELL NOW OR HOLD — prices expected to stay stable")
    confidence_score: float = Field(0.90, ge=0.0, le=1.0)
    market_risk: str = Field("LOW", description="LOW | MEDIUM | HIGH")
    sell_timing_hint: str = Field("", description="Short caps instruction")
    expected_price_change_hint: str = Field(
        "",
        description="Plain-language expectation vs recent prices.",
    )


class PricePredictionRequest(BaseModel):
    """Input for price forecast + Decision Engine recommendation."""

    market: str = Field("Dambulla", description="Market location: Dambulla or Pettah.")
    type: str = Field("Retail", description="Series type: Retail or Wholesale.")
    location: Optional[str] = Field(
        "Dambulla-Retail",
        description="Market-Type location string, e.g. Dambulla-Retail, Dambulla-Wholesale, Pettah-Retail, Pettah-Wholesale.",
    )
    target_date: Optional[date] = Field(
        None,
        description="Optional target date (YYYY-MM-DD). If omitted, uses latest available dataset date.",
    )
    forecast_horizon_days: int = Field(14, ge=1, le=30, description="Forecast horizon days (default 14).")
    currency: str = Field("LKR/kg", description="Currency label")

    @model_validator(mode="before")
    @classmethod
    def _resolve_market_type(cls, data: Any) -> Any:
        if isinstance(data, dict):
            loc = data.get("location")
            mkt = data.get("market")
            tp = data.get("type")

            if loc and isinstance(loc, str):
                loc_clean = loc.strip()
                if "-" in loc_clean:
                    parts = loc_clean.split("-", 1)
                    data["market"] = parts[0].strip()
                    data["type"] = parts[1].strip()
                elif " " in loc_clean and not mkt:
                    parts = loc_clean.split(" ", 1)
                    data["market"] = parts[0].strip()
                    data["type"] = parts[1].strip()
                elif not mkt:
                    data["market"] = loc_clean
                    if not tp:
                        data["type"] = "Retail"
        return data


class PricePredictionResponse(BaseModel):
    """Unified Decision Engine response payload."""

    series: str = Field(..., description="Series label (e.g. Dambulla-Retail)")
    market: str = Field(..., description="Market name (e.g. Dambulla)")
    type: str = Field(..., description="Series type (e.g. Retail)")
    request_date: str = Field(..., description="Date prediction request was made (YYYY-MM-DD)")
    target_date: Optional[str] = Field(None, description="Requested target selling date (YYYY-MM-DD), if provided")
    current_price_lkr: float = Field(..., description="Recent observed actual price (LKR/kg)")
    data_as_of_date: str = Field(..., description="Max cutoff date of historical dataset")
    dataset_coverage: str = Field(..., description="Historical dataset date range coverage")
    forecast_dates: List[str] = Field(default_factory=list, description="ISO calendar dates for each forecast day computed from data_as_of_date + 1")
    forecast_start_date: str = Field(..., description="First forecast horizon date (data_as_of_date + 1 day)")
    forecast_end_date: str = Field(..., description="Last forecast horizon date")
    forecast_period_label: str = Field(..., description="Human-readable forecast date range label (e.g., March 11 – March 24, 2026)")
    recommendation: str = Field(..., description="MONITOR | HOLD | SELL NOW | SELL NOW OR HOLD — prices expected to stay stable")
    reasoning: str = Field(..., description="Plain-language farmer explanation")
    action_code: str = Field("STABLE", description="Explicit categorical recommendation: SELL_NOW | HOLD | STABLE | MONITOR")
    peak_price_lkr: Optional[float] = Field(None, description="Maximum forecast price in horizon (LKR/kg)")
    peak_day: Optional[int] = Field(None, description="1-indexed forecast day of maximum price")
    peak_change_pct: Optional[float] = Field(None, description="Percentage change of peak price vs current price")
    terminal_change_pct: Optional[float] = Field(None, description="Percentage change of Day-14 price vs current price")
    post_peak_drop_pct: Optional[float] = Field(None, description="Percentage drop from peak to Day-14 price")
    trend: Optional[str] = Field(None, description="Overall forecast trajectory trend: RISING | DECLINING | STABLE")
    optimal_sell_day: Optional[int] = Field(None, description="Recommended optimal sell day (1-indexed)")
    optimal_sell_price_lkr: Optional[float] = Field(None, description="Expected price on optimal sell day (LKR/kg)")


    # Forecast arrays
    base_lstm_forecast: List[float] = Field(..., description="Raw LSTM base predictions per horizon day")
    weather_adjusted_forecast: List[float] = Field(..., description="Weather-adjusted predictions per horizon day")
    predicted_prices: List[str] = Field(..., description="Weather-adjusted forecast strings for UI charts")
    predicted_price: float = Field(..., description="Day 1 weather-adjusted forecast price")

    # Weather & Corroborated Signal fields
    weather_flag_level: str = Field(..., description="none | moderate | severe")
    d14_cum_rain_mm: float = Field(..., description="Anuradhapura 14-day lagged cumulative rainfall change (mm)")
    regional_weather_impact: Optional[Dict[str, Any]] = Field(None, description="Multi-station Sri Lankan regional weather impact analysis")
    corroborated_signals: Optional[Dict[str, Any]] = Field(None, description="Multi-source corroboration of weather and news intelligence")

    # News event flag fields
    news_flag_level: str = Field("none", description="none | watch | alert")
    news_events: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant qualitative news events")

    # SHAP Explainability field
    shap_explanation: Optional[Dict[str, Any]] = Field(None, description="SHAP timestep attributions and summary")



    # Anomaly fields
    is_anomaly: bool = Field(..., description="True if IsolationForest residual anomaly detected")
    anomaly_severity: str = Field(..., description="NORMAL | MODERATE | HIGH")
    anomaly_score: float = Field(..., description="IsolationForest sample score")
    residual_lkr: float = Field(..., description="Residual: actual price minus 1-day prediction")

    # Metrics & Driver shares
    pct_change_day1: float = Field(..., description="Day 1 forecast % change vs current price")
    volatility_threshold_pct: float = Field(..., description="Empirical active-days 1-sigma volatility threshold %")
    driver_share_lstm_pct: float = Field(..., description="Base LSTM contribution %")
    driver_share_weather_pct: float = Field(..., description="Weather contribution %")
    day1_forecast_lkr: float = Field(..., description="Day 1 forecast price")
    day14_forecast_lkr: float = Field(..., description="Day 14 forecast price")

    currency: str = "LKR/kg"
    forecast_horizon_days: int = 14


def compute_horizon_for_target(target: Optional[date], default_horizon: int) -> tuple[int, Optional[str], Optional[date]]:
    """Map optional target_date to horizon days."""
    if target is None:
        return default_horizon, None, None

    today = datetime.now(TZ_COLOMBO).date()
    days_ahead = (target - today).days
    if days_ahead < 0:
        raise ValueError("target_date cannot be in the past (Asia/Colombo calendar).")
    if days_ahead == 0:
        days_ahead = 1

    max_days = 16
    note = None
    if days_ahead > max_days:
        note = f"target_date is {days_ahead} days ahead; capped at {max_days} days."
        days_ahead = max_days

    return days_ahead, note, target

