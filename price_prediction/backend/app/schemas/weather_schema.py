from typing import List, Optional

from pydantic import BaseModel, Field


class WeatherResponse(BaseModel):
    """Weather insight for the selected area (Open-Meteo forecast)."""

    location: str
    weather_signal: str
    expected_temperature_celsius: float
    storm_risk_level: str
    market_impact_score: float
    price_effect: str = Field(
        ...,
        description="Rough price pressure label: UP, SLIGHTLY_UP, STABLE, DOWN",
    )
    reason: str = Field(..., description="Plain English explanation for farmers.")
    data_source: str = Field(..., description="Open-Meteo API or fallback if the call failed.")
    forecast_dates: List[str] = Field(default_factory=list, description="ISO dates for the forecast window.")
    daily_rainfall: List[float] = Field(
        default_factory=list,
        description="Daily precipitation_sum (mm) for each forecast date.",
    )
    impact: str = Field(
        ...,
        description="Business impact bucket: HIGH, MEDIUM, LOW, NONE, or UNKNOWN on fallback.",
    )
    # Extra context for explainable AI (when Open-Meteo returns humidity).
    humidity_avg_pct: Optional[float] = Field(
        None,
        description="Average daily relative humidity (%) over the forecast window.",
    )
    area_used_for_forecast: str = Field(
        "",
        description="Human-readable name tied to the coordinates used (may differ slightly from user text).",
    )
    water_stress_level: Optional[str] = Field(
        "NORMAL",
        description="NORMAL | MODERATE_STRESS | SEVERE_DROUGHT | EXCESS_WATER",
    )
    heat_stress_level: Optional[str] = Field(
        "NORMAL",
        description="NORMAL | MODERATE_HEAT | EXTREME_HEAT",
    )
    agricultural_favourability: Optional[str] = Field(
        "FAVOURABLE",
        description="FAVOURABLE | MODERATE | WATER_STRESS | EXCESS_WATER",
    )
    agricultural_impact: Optional[dict] = Field(
        None,
        description="Structured agricultural assessment (water availability, time horizon, missing future data).",
    )

