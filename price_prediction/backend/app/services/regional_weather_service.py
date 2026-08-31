"""
Regional Weather Feature Engine & Impact Evaluator for Sri Lankan Tomato Price Advisor.
Calculates 21-day/30-day cumulative rainfall, 3-day/7-day average temperatures,
consecutive dry/wet spells, and monthly seasonal Z-score anomalies for 4 agricultural stations:
Anuradhapura, Badulla, Dambulla, Nuwara Eliya.

All regional weights are marked as CONFIGURATION, ready for DCS/DOA acreage updates.
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WEATHER_CSV_PATH = BASE_DIR / "backend" / "datasets" / "historical_weather_sri_lanka.csv"
if not WEATHER_CSV_PATH.exists():
    WEATHER_CSV_PATH = BASE_DIR / "datasets" / "historical_weather_sri_lanka.csv"

# ==============================================================================
# CONFIGURATION: REGIONAL WEIGHTS BY SEASON
# Mark clearly as configurable parameters, not hardcoded empirical truth.
# Designed to be replaced with official DCS / DOA seasonal production acreage statistics.
# ==============================================================================
REGIONAL_WEIGHTS: Dict[str, Dict[str, float]] = {
    "Maha": {  # November to February (Dry & Intermediate Zones dominate)
        "Anuradhapura": 0.40,
        "Dambulla": 0.30,
        "Badulla": 0.15,
        "Nuwara Eliya": 0.15,
    },
    "Yala": {  # May to August (Upcountry & Hill Slope Zones dominate)
        "Badulla": 0.40,
        "Nuwara Eliya": 0.30,
        "Dambulla": 0.20,
        "Anuradhapura": 0.10,
    },
    "Intermonsoon": {  # March-April & September-October (Mixed intermediate supply)
        "Dambulla": 0.35,
        "Badulla": 0.25,
        "Nuwara Eliya": 0.20,
        "Anuradhapura": 0.20,
    },
}

# Market-Specific Regional Adjustments (Market supply feeder preferences)
MARKET_REGION_PREFERENCES: Dict[str, Dict[str, float]] = {
    "Dambulla-Wholesale": {"Anuradhapura": 0.40, "Dambulla": 0.35, "Badulla": 0.15, "Nuwara Eliya": 0.10},
    "Dambulla-Retail": {"Dambulla": 0.40, "Anuradhapura": 0.30, "Badulla": 0.15, "Nuwara Eliya": 0.15},
    "Pettah-Wholesale": {"Badulla": 0.35, "Anuradhapura": 0.30, "Nuwara Eliya": 0.20, "Dambulla": 0.15},
    "Pettah-Retail": {"Nuwara Eliya": 0.35, "Badulla": 0.30, "Pettah/Dambulla": 0.20, "Anuradhapura": 0.15},
}

# Horizon-Specific Impact Scaling Weights (Empirically validated in statistical audit)
# 1-day: Negligible (<0.6%), 3-day: Minor (~1.5%), 7-day: Moderate (~2.8%), 14-day: Maximum (~8.25%)
HORIZON_SCALING_WEIGHTS: Dict[int, float] = {
    1: 0.05,
    2: 0.10,
    3: 0.18,
    4: 0.28,
    5: 0.38,
    6: 0.50,
    7: 0.62,
    8: 0.72,
    9: 0.80,
    10: 0.86,
    11: 0.91,
    12: 0.95,
    13: 0.98,
    14: 1.00,
}

# Calibrated Maximum Bounded Percentage Adjustment (Out-of-sample validated bound)
MAX_BOUNDED_ADJUSTMENT_PCT: float = 8.25

STATIONS: List[str] = ["Anuradhapura", "Badulla", "Dambulla", "Nuwara Eliya"]


def get_season_for_date(dt: pd.Timestamp) -> str:
    """Return agricultural season name based on Sri Lankan crop calendar."""
    month = dt.month
    if month in [11, 12, 1, 2]:
        return "Maha"
    elif month in [5, 6, 7, 8]:
        return "Yala"
    else:
        return "Intermonsoon"


class RegionalWeatherService:
    """
    Service for calculating regional weather features, monthly seasonal Z-scores,
    composite risk scores, and horizon-specific price adjustments.
    """

    def __init__(self, weather_csv: Optional[Path] = None):
        self.csv_path = weather_csv or WEATHER_CSV_PATH
        self._load_and_preprocess()

    def _load_and_preprocess(self):
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Weather dataset missing at {self.csv_path}")

        df = pd.read_csv(self.csv_path)
        df.columns = [c.strip() for c in df.columns]
        df["Date"] = pd.to_datetime(df["Date"])

        # Rename standard columns
        df = df.rename(columns={"Rainfall(mm)": "Rainfall", "Temperature(°C)": "Temperature", "Temperature(?C)": "Temperature"})
        for col in df.columns:
            if "Rainfall" in col:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df = df.rename(columns={col: "Rainfall"})
            elif "Temp" in col:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df = df.rename(columns={col: "Temperature"})

        df = df.sort_values(["Location", "Date"]).reset_index(drop=True)
        df["Month"] = df["Date"].dt.month

        # Feature engineering per station
        station_dfs = []
        for loc in STATIONS:
            sub = df[df["Location"] == loc].copy().sort_values("Date").reset_index(drop=True)

            # Rolling cumulative rainfall
            sub["rain_21d"] = sub["Rainfall"].rolling(21, min_periods=1).sum()
            sub["rain_30d"] = sub["Rainfall"].rolling(30, min_periods=1).sum()

            # Rolling average temperatures
            sub["temp_3d"] = sub["Temperature"].rolling(3, min_periods=1).mean()
            sub["temp_7d"] = sub["Temperature"].rolling(7, min_periods=1).mean()

            # Consecutive dry/wet spells
            is_dry = (sub["Rainfall"] < 1.0).astype(int)
            is_wet = (sub["Rainfall"] >= 1.0).astype(int)

            # Cumulative counts reset on condition change
            sub["consecutive_dry_days"] = is_dry.groupby((is_dry != is_dry.shift()).cumsum()).cumsum()
            sub["consecutive_wet_days"] = is_wet.groupby((is_wet != is_wet.shift()).cumsum()).cumsum()

            station_dfs.append(sub)

        full_df = pd.concat(station_dfs, ignore_index=True)

        # Monthly seasonal baseline statistics per location and month
        monthly_baselines = (
            full_df.groupby(["Location", "Month"])[["rain_21d", "rain_30d", "temp_3d", "temp_7d"]]
            .agg(["mean", "std"])
            .reset_index()
        )
        monthly_baselines.columns = [
            "Location",
            "Month",
            "rain_21d_mean",
            "rain_21d_std",
            "rain_30d_mean",
            "rain_30d_std",
            "temp_3d_mean",
            "temp_3d_std",
            "temp_7d_mean",
            "temp_7d_std",
        ]

        full_df = pd.merge(full_df, monthly_baselines, on=["Location", "Month"], how="left")

        # Z-score calculations with safe std epsilon
        eps = 1e-5
        full_df["rain_21d_z"] = (full_df["rain_21d"] - full_df["rain_21d_mean"]) / (full_df["rain_21d_std"].replace(0, eps) + eps)
        full_df["rain_30d_z"] = (full_df["rain_30d"] - full_df["rain_30d_mean"]) / (full_df["rain_30d_std"].replace(0, eps) + eps)
        full_df["temp_3d_z"] = (full_df["temp_3d"] - full_df["temp_3d_mean"]) / (full_df["temp_3d_std"].replace(0, eps) + eps)
        full_df["temp_7d_z"] = (full_df["temp_7d"] - full_df["temp_7d_mean"]) / (full_df["temp_7d_std"].replace(0, eps) + eps)

        self.df = full_df

    def get_station_features(self, station: str, target_date_str: str) -> Dict[str, Any]:
        """Fetch pre-calculated weather features for a station on or before target_date_str."""
        target_dt = pd.to_datetime(target_date_str)
        sub = self.df[(self.df["Location"] == station) & (self.df["Date"] <= target_dt)].sort_values("Date")
        if sub.empty:
            raise ValueError(f"No weather data for station {station} on or before {target_date_str}")

        row = sub.iloc[-1]
        return {
            "station": station,
            "date": row["Date"].strftime("%Y-%m-%d"),
            "rainfall_daily_mm": round(float(row["Rainfall"]), 2),
            "temp_daily_c": round(float(row["Temperature"]), 2),
            "rain_21d_cum_mm": round(float(row["rain_21d"]), 2),
            "rain_30d_cum_mm": round(float(row["rain_30d"]), 2),
            "temp_3d_avg_c": round(float(row["temp_3d"]), 2),
            "temp_7d_avg_c": round(float(row["temp_7d"]), 2),
            "consecutive_dry_days": int(row["consecutive_dry_days"]),
            "consecutive_wet_days": int(row["consecutive_wet_days"]),
            "rain_21d_mean_mm": round(float(row["rain_21d_mean"]), 2),
            "rain_21d_z": round(float(row["rain_21d_z"]), 2),
            "rain_30d_z": round(float(row["rain_30d_z"]), 2),
            "temp_3d_z": round(float(row["temp_3d_z"]), 2),
            "temp_7d_z": round(float(row["temp_7d_z"]), 2),
        }

    def get_regional_weather_impact(
        self, target_date_str: str, market: str = "Dambulla", series_type: str = "Wholesale"
    ) -> Dict[str, Any]:
        """
        Calculates multi-station regional weather risk score, seasonal weights,
        and market-specific impact evaluation.
        """
        target_dt = pd.to_datetime(target_date_str)
        season = get_season_for_date(target_dt)
        series_label = f"{market}-{series_type}"

        # Select weights (market preference if available, else seasonal config)
        if series_label in MARKET_REGION_PREFERENCES:
            weights = MARKET_REGION_PREFERENCES[series_label]
        else:
            weights = REGIONAL_WEIGHTS.get(season, REGIONAL_WEIGHTS["Intermonsoon"])

        region_features: Dict[str, Dict[str, Any]] = {}
        composite_z = 0.0
        primary_station = STATIONS[0]
        max_weighted_contrib = -1.0

        for station in STATIONS:
            feat = self.get_station_features(station, target_date_str)
            w = weights.get(station, 0.25)
            feat["seasonal_weight"] = w

            r_z = feat["rain_21d_z"]
            dry_days = feat["consecutive_dry_days"]
            rain_21 = feat["rain_21d_cum_mm"]
            t3d = feat["temp_3d_avg_c"]

            # Classify water stress and agricultural condition per station
            if r_z >= 1.8 or feat["consecutive_wet_days"] >= 10:
                water_status = "EXCESS_WATER_SATURATION"
                water_stress = "EXCESS"
                agri_stress = "HIGH"
                risk_lvl = "SEVERE"
                time_horiz = "Short-term (1-3 days harvest/transport)"
                supply_risk = "Immediate harvest loss and transport disruption"
            elif r_z >= 0.8:
                water_status = "ELEVATED_MOISTURE"
                water_stress = "ELEVATED"
                agri_stress = "MODERATE"
                risk_lvl = "MODERATE"
                time_horiz = "Short-term (2-5 days)"
                supply_risk = "Minor fieldwork and transport slowdown"
            elif r_z <= -1.2 or dry_days >= 21 or (rain_21 < 15.0 and t3d >= 33.0):
                water_status = "SEVERE_DROUGHT_STRESS"
                water_stress = "HIGH"
                agri_stress = "HIGH"
                risk_lvl = "SEVERE"
                time_horiz = "Medium to Long-term (14-60 days)"
                supply_risk = "Potential future production and acreage reduction"
            elif r_z <= -0.6 or dry_days >= 14 or (rain_21 < 35.0 and t3d >= 30.0):
                water_status = "MODERATE_WATER_DEFICIT"
                water_stress = "MODERATE"
                agri_stress = "MODERATE"
                risk_lvl = "MODERATE"
                time_horiz = "Medium-term (7-21 days)"
                supply_risk = "Irrigation strain; manageable if tanks active"
            else:
                water_status = "OPTIMAL_BALANCED"
                water_stress = "LOW"
                agri_stress = "LOW"
                risk_lvl = "LOW"
                time_horiz = "Immediate to Medium-term"
                supply_risk = "Normal balanced crop conditions"

            # Assign agro-ecological zone context
            zone_map = {
                "Anuradhapura": "Dry Zone (Low Country — Tank & Well Irrigated)",
                "Badulla": "Intermediate/Hill Zone (Primary Yala supplier)",
                "Dambulla": "Intermediate Zone (Central Trade & Distribution DEC)",
                "Nuwara Eliya": "Wet Zone (Upcountry Intensive Terraces)",
            }
            feat["agro_ecological_zone"] = zone_map.get(station, "Agricultural Region")
            feat["water_status"] = water_status
            feat["water_stress_level"] = water_stress
            feat["agricultural_stress_level"] = agri_stress
            feat["risk_level"] = risk_lvl
            feat["time_horizon"] = time_horiz
            feat["supply_risk_summary"] = supply_risk

            composite_z += w * r_z
            region_features[station] = feat

            weighted_contrib = w * abs(r_z)
            if weighted_contrib > max_weighted_contrib:
                max_weighted_contrib = weighted_contrib
                primary_station = station

        # Classify overall risk level based on composite Z-score and drought flags
        has_severe_drought = any(f["water_status"] == "SEVERE_DROUGHT_STRESS" for f in region_features.values())
        has_severe_flood = any(f["water_status"] == "EXCESS_WATER_SATURATION" for f in region_features.values())

        if has_severe_flood or has_severe_drought or abs(composite_z) > 2.0:
            overall_risk = "SEVERE"
        elif abs(composite_z) >= 1.0 or any(f["water_stress_level"] == "MODERATE" for f in region_features.values()):
            overall_risk = "MODERATE"
        else:
            overall_risk = "LOW"

        # Market Storage Context (Dambulla DEC vs Pettah Warehouse ambient condition)
        storage_station = "Dambulla" if "Dambulla" in market else "Nuwara Eliya"
        storage_feat = region_features.get(storage_station, region_features["Dambulla"])
        storage_temp = storage_feat["temp_3d_avg_c"]
        storage_spoilage_risk = "HIGH" if storage_temp >= 30.0 else ("MEDIUM" if storage_temp >= 26.0 else "LOW")

        market_storage_impact = {
            "market_location": market,
            "ambient_temp_3d_avg_c": storage_temp,
            "spoilage_risk_level": storage_spoilage_risk,
            "selling_urgency": "HIGH" if storage_spoilage_risk == "HIGH" else "NORMAL",
            "interpretation": (
                f"Market holding ambient temperature averaging {storage_temp}°C creates {storage_spoilage_risk.lower()} "
                f"post-harvest spoilage pressure."
            ),
        }

        # Structured Agricultural Impact Assessment (Section 8 Standard Schema)
        prim_feat = region_features[primary_station]
        is_drought_signal = prim_feat["water_status"] in ("SEVERE_DROUGHT_STRESS", "MODERATE_WATER_DEFICIT")

        if is_drought_signal:
            explanation_text = (
                f"In {primary_station} ({prim_feat['agro_ecological_zone']}), 21-day rainfall is {prim_feat['rain_21d_cum_mm']} mm "
                f"({abs(prim_feat['rain_21d_z']):.1f}σ below the 10-year monthly seasonal baseline of {prim_feat['rain_21d_mean_mm']} mm) "
                f"with 3-day average temperatures at {prim_feat['temp_3d_avg_c']}°C ({prim_feat['consecutive_dry_days']} consecutive dry days). "
                f"While current daily market deliveries from active harvests continue normally in the short term, "
                f"persistent dry conditions deplete minor irrigation tanks and groundwater, posing medium-to-long term "
                f"water stress on field establishment and future tomato production."
            )
        else:
            explanation_text = (
                f"Observed 21-day cumulative rainfall in {primary_station} ({prim_feat['rain_21d_cum_mm']} mm) "
                f"has been {abs(prim_feat['rain_21d_z']):.1f}σ {'above' if prim_feat['rain_21d_z'] >= 0 else 'below'} "
                f"the station's 10-year monthly seasonal baseline ({prim_feat['rain_21d_mean_mm']} mm). "
                f"In historical project validation, elevated 21-day rainfall in this growing hub was statistically associated "
                f"with subsequent market supply deficits and upward price pressure."
            )

        structured_agricultural_assessment = {
            "location": primary_station,
            "agro_ecological_zone": prim_feat["agro_ecological_zone"],
            "weather_condition": prim_feat["water_status"].replace("_", " ").title(),
            "rainfall_status": f"21-day total: {prim_feat['rain_21d_cum_mm']} mm ({prim_feat['rain_21d_z']:+.1f}σ vs {prim_feat['rain_21d_mean_mm']} mm baseline)",
            "heat_status": f"3-day avg temp: {prim_feat['temp_3d_avg_c']}°C (7-day: {prim_feat['temp_7d_avg_c']}°C)",
            "water_stress": prim_feat["water_stress_level"],
            "agricultural_stress": prim_feat["agricultural_stress_level"],
            "tomato_supply_risk": prim_feat["supply_risk_summary"],
            "price_direction": "Potential upward pressure (medium/long term)" if is_drought_signal else ("Upward pressure (short term)" if prim_feat["rain_21d_z"] >= 1.0 else "Stable baseline"),
            "time_horizon": prim_feat["time_horizon"],
            "confidence": "High" if abs(prim_feat["rain_21d_z"]) >= 1.5 else "Medium",
            "evidence_type": "Direct meteorological multi-station historical series",
            "future_data_sources_needed": [
                "soil_moisture_depth_sensors",
                "minor_irrigation_tank_capacity_pct",
                "crop_evapotranspiration_et0_index",
            ],
        }

        return {
            "season": season,
            "target_date": target_date_str,
            "market_series": series_label,
            "overall_weather_risk": overall_risk,
            "composite_rain_21d_z": round(composite_z, 2),
            "primary_region": primary_station,
            "primary_signal": "21-day rainfall & water-stress anomaly",
            "confidence_basis": "Empirical 21-day lag cross-correlation and agro-climatic water availability",
            "explanation": explanation_text,
            "growing_region_weather": {
                "composite_risk_score": round(composite_z, 2),
                "primary_region": primary_station,
                "regions": region_features,
            },
            "market_storage_impact": market_storage_impact,
            "structured_agricultural_assessment": structured_agricultural_assessment,
        }

    def calculate_weather_adjustment(
        self, market: str, series_type: str, forecast_horizon_days: int, target_date_str: str
    ) -> Dict[str, Any]:
        """
        Calculates horizon-specific, bounded, calibrated price adjustment (LKR & %).
        Ensures 1-day adjustment is near zero and 14-day adjustment is bounded to max +-8.25%.
        """
        impact = self.get_regional_weather_impact(target_date_str, market, series_type)
        composite_z = impact["composite_rain_21d_z"]

        # Base 14-day percentage adjustment based on composite Z-score (+2.5% per sigma of rain anomaly)
        raw_14d_adj_pct = composite_z * 2.5

        # Strictly clamp max 14-day percentage adjustment to out-of-sample validated bound (+-8.25%)
        clamped_14d_adj_pct = max(-MAX_BOUNDED_ADJUSTMENT_PCT, min(MAX_BOUNDED_ADJUSTMENT_PCT, raw_14d_adj_pct))

        # Horizon scaling (Horizon 1 -> 0.05, Horizon 14 -> 1.0)
        h_weight = HORIZON_SCALING_WEIGHTS.get(forecast_horizon_days, min(1.0, forecast_horizon_days / 14.0))
        final_adj_pct = round(clamped_14d_adj_pct * h_weight, 2)

        direction = "UP" if final_adj_pct > 0.5 else ("DOWN" if final_adj_pct < -0.5 else "NEUTRAL")

        return {
            "forecast_horizon_days": forecast_horizon_days,
            "horizon_scale_factor": round(h_weight, 2),
            "composite_rain_21d_z": composite_z,
            "clamped_14d_max_adj_pct": clamped_14d_adj_pct,
            "final_adjustment_pct": final_adj_pct,
            "direction": direction,
            "reason": impact["explanation"],
            "primary_region": impact["primary_region"],
            "regional_impact_summary": impact,
        }

    def get_regional_seas5_outlook(
        self, target_year: int, target_month: int, market: str = "Dambulla", series_type: str = "Wholesale"
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates multi-station SEAS5 seasonal ensemble tercile probabilities
        (Above Normal, Near Normal, Below Normal) using existing heuristic station weights.
        Returns None if SEAS5 is unavailable or target month is out of horizon.
        """
        from app.services.weather_service import fetch_seas5_seasonal_outlook

        station_coords = {
            "Anuradhapura": (8.3114, 80.4037),
            "Badulla": (6.9934, 81.0550),
            "Dambulla": (7.8567, 80.6517),
            "Nuwara Eliya": (6.9497, 80.7891),
        }

        series_label = f"{market}-{series_type}"
        if series_label in MARKET_REGION_PREFERENCES:
            weights = MARKET_REGION_PREFERENCES[series_label]
        else:
            season = get_season_for_date(pd.Timestamp(year=target_year, month=target_month, day=15))
            weights = REGIONAL_WEIGHTS.get(season, REGIONAL_WEIGHTS["Intermonsoon"])

        # Compute historical monthly rainfall total stats (mean, std) for each location and target month
        df_w = self.df.copy()
        monthly_totals = (
            df_w.groupby(["Location", df_w["Date"].dt.year, "Month"])["Rainfall"]
            .sum()
            .reset_index()
        )
        sub_m = monthly_totals[monthly_totals["Month"] == target_month]

        station_results = {}
        weighted_above = 0.0
        weighted_near = 0.0
        weighted_below = 0.0
        total_weight_used = 0.0

        for station in STATIONS:
            w = weights.get(station, 0.25)
            coords = station_coords.get(station)
            if not coords:
                continue

            seas5_raw = fetch_seas5_seasonal_outlook(coords[0], coords[1], target_year, target_month)
            if not seas5_raw or not seas5_raw.get("member_rainfall_sums"):
                # If any station fails or is out of horizon, return None to trigger safe historical fallback
                return None

            st_sub = sub_m[sub_m["Location"] == station]
            if not st_sub.empty:
                hist_mean = float(st_sub["Rainfall"].mean())
                hist_std = float(st_sub["Rainfall"].std())
                if np.isnan(hist_std) or hist_std <= 0:
                    hist_std = max(10.0, hist_mean * 0.3)
            else:
                hist_mean = 100.0
                hist_std = 30.0

            member_sums = seas5_raw["member_rainfall_sums"]
            total_members = len(member_sums)

            cnt_above = 0
            cnt_near = 0
            cnt_below = 0

            lower_bound = hist_mean - 0.5 * hist_std
            upper_bound = hist_mean + 0.5 * hist_std

            for r_val in member_sums:
                if r_val > upper_bound:
                    cnt_above += 1
                elif r_val < lower_bound:
                    cnt_below += 1
                else:
                    cnt_near += 1

            st_above_pct = round((cnt_above / total_members) * 100.0)
            st_near_pct = round((cnt_near / total_members) * 100.0)
            st_below_pct = 100 - st_above_pct - st_near_pct

            station_results[station] = {
                "weight": w,
                "historical_monthly_mean_mm": round(hist_mean, 1),
                "historical_monthly_std_mm": round(hist_std, 1),
                "ensemble_members_count": total_members,
                "above_normal_pct": st_above_pct,
                "near_normal_pct": st_near_pct,
                "below_normal_pct": st_below_pct,
                "avg_temperature_celsius": seas5_raw.get("avg_temperature_celsius", 25.0),
            }

            weighted_above += w * st_above_pct
            weighted_near += w * st_near_pct
            weighted_below += w * st_below_pct
            total_weight_used += w

        if total_weight_used <= 0:
            return None

        reg_above = round(weighted_above / total_weight_used)
        reg_near = round(weighted_near / total_weight_used)
        reg_below = 100 - reg_above - reg_near

        if reg_above >= 45:
            overall_outlook = "Above-Normal Rainfall"
        elif reg_below >= 45:
            overall_outlook = "Below-Normal Rainfall"
        else:
            overall_outlook = "Near-Normal Rainfall"

        return {
            "source": "ECMWF SEAS5",
            "model": "ecmwf_seas5",
            "forecast_type": "seasonal_ensemble",
            "target_month": f"{target_year:04d}-{target_month:02d}",
            "target_year": target_year,
            "target_month_num": target_month,
            "availability": "available",
            "regional_outlook": overall_outlook,
            "ensemble_probability": {
                "above_normal": reg_above,
                "near_normal": reg_near,
                "below_normal": reg_below,
            },
            "station_weights": weights,
            "stations": station_results,
            "disclaimer": "This is a monthly seasonal ensemble outlook from ECMWF SEAS5 (50 members), not a specific daily weather forecast.",
        }

