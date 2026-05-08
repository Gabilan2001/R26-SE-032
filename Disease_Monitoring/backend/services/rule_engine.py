"""
Rule-Based Engine
Calculates:
- Daily severity drop rate
- Weather-adjusted risk score
- TRR (Treatment Response Rate)
- Final verdict: SUCCESS / PARTIAL / FAILURE
"""

def compute_daily_output(day: int, severity_a: float,
                          severity_b: float,
                          weather: dict,
                          prev_severity_a: float = None,
                          prev_severity_b: float = None) -> dict:
    """
    Runs after each day upload.
    Returns daily analysis output.
    """
    risk_score = weather.get("risk_score", 0)
    risk_level = weather.get("risk_level", "UNKNOWN")
    humidity   = weather.get("details", {}).get("humidity", 0)
    rainfall   = weather.get("details", {}).get("rainfall_1h", 0)

    # ── Combined Risk Assessment ──────────────────────────────────────────────
    # Formula: (Max Severity * 0.6) + (Weather Risk * 0.4)
    max_sev = max(severity_a, severity_b)
    combined_score = round((max_sev * 0.6) + (risk_score * 0.4), 2)
    
    if max_sev > 50 or combined_score > 60:
        combined_level = "HIGH"
    elif combined_score > 25:
        combined_level = "MEDIUM"
    else:
        combined_level = "LOW"

    result = {
        "day":                  day,
        "severity_a":           severity_a,
        "severity_b":           severity_b,
        "total_severity":       round(severity_a + severity_b, 2),
        "weather_risk":         risk_score,
        "weather_risk_level":   risk_level,
        "combined_risk_score":  combined_score,
        "combined_risk_level":  combined_level,
        "alerts":               []
    }

    # Day 1: baseline — just record and check weather
    if day == 1:
        if risk_score > 70:
            result["alerts"].append(
                "High fungal risk on treatment day. "
                "Treatment effectiveness may be reduced."
            )
        if rainfall > 10:
            result["alerts"].append(
                f"Heavy rainfall ({rainfall}mm) detected. "
                "Contact fungicide may wash away. "
                "Consider systemic fungicide."
            )
        result["status"] = "BASELINE_RECORDED"

    # Day 3: Detailed Monitoring Check
    elif day == 3:
        if prev_severity_a is not None:
            # Disease A Monitoring
            drop_a = prev_severity_a - severity_a
            daily_drop_a = round(drop_a / 2, 2)
            result["daily_drop_a"] = daily_drop_a
            
            if drop_a > 0:
                status_a = "ON_TRACK" if daily_drop_a >= 1.5 else "SLOW_RECOVERY"
            elif drop_a == 0:
                status_a = "STAGNANT"
            else:
                status_a = "WORSENING"
            
            result["monitoring_status_a"] = status_a
            
            # Disease B Monitoring
            drop_b = (prev_severity_b or 0) - severity_b
            daily_drop_b = round(drop_b / 2, 2)
            result["daily_drop_b"] = daily_drop_b
            
            if drop_b > 0:
                status_b = "ON_TRACK" if daily_drop_b >= 1.5 else "SLOW_RECOVERY"
            elif drop_b == 0:
                status_b = "STAGNANT"
            else:
                status_b = "WORSENING"
            
            result["monitoring_status_b"] = status_b

            # Add Specific Monitoring Alerts
            if status_a in ["STAGNANT", "WORSENING"] or status_b in ["STAGNANT", "WORSENING"]:
                result["alerts"].append(
                    "CRITICAL: Treatment is NOT stopping the disease. "
                    "Infection is spreading or stagnant. Check application method."
                )
            elif status_a == "SLOW_RECOVERY" or status_b == "SLOW_RECOVERY":
                result["alerts"].append(
                    "CAUTION: Recovery is slower than 1.5% per day. "
                    "High risk of failing Day 7 success target."
                )
            else:
                result["alerts"].append("GOOD PROGRESS: Treatment is working effectively.")

            # Weather impact on monitoring
            if risk_score > 60 and status_a != "ON_TRACK":
                result["alerts"].append(
                    "Weather risk is HIGH. Current slow recovery is likely "
                    "due to high humidity/rain assisting disease spread."
                )

        result["status"] = "PROGRESS_MONITORED"

    # Day 7: final assessment
    elif day == 7:
        result["status"] = "READY_FOR_TRR"

    return result


def compute_trr(day1_sev_a: float, day7_sev_a: float,
                day1_sev_b: float, day7_sev_b: float,
                weather_history: list = None) -> dict:
    """
    Compute Treatment Response Rate after Day 7.
    
    TRR = (Day1_Severity - Day7_Severity) / Day1_Severity × 100
    
    Verdict:
    SUCCESS:         TRR > 20%
    PARTIAL SUCCESS: TRR 5-20%
    FAILURE:         TRR < 5%
    """

    # Calculate TRR for each disease
    def calc_trr(start, end):
        if start == 0:
            return 0.0
        return round(((start - end) / start) * 100, 2)

    trr_a = calc_trr(day1_sev_a, day7_sev_a)
    trr_b = calc_trr(day1_sev_b, day7_sev_b)

    # Overall TRR (weighted average)
    if day1_sev_a + day1_sev_b > 0:
        weight_a  = day1_sev_a / (day1_sev_a + day1_sev_b)
        weight_b  = day1_sev_b / (day1_sev_a + day1_sev_b)
        overall   = round(trr_a * weight_a + trr_b * weight_b, 2)
    else:
        overall   = 0.0

    # Verdict classification
    def classify(trr):
        if trr > 20:  return "SUCCESS"
        if trr >= 5:  return "PARTIAL"
        return "FAILURE"

    verdict_a = classify(trr_a)
    verdict_b = classify(trr_b)

    # Overall verdict (worst case wins)
    if "FAILURE" in [verdict_a, verdict_b]:
        overall_verdict = "FAILURE"
    elif "PARTIAL" in [verdict_a, verdict_b]:
        overall_verdict = "PARTIAL"
    else:
        overall_verdict = "SUCCESS"

    # Check weather impact on failure
    weather_caused_failure = False
    if overall_verdict == "FAILURE" and weather_history:
        total_rain = sum(
            w.get("details", {}).get("rainfall_1h", 0)
            for w in weather_history
        )
        if total_rain > 10:
            weather_caused_failure = True

    result = {
        "trr_disease_a":        trr_a,
        "trr_disease_b":        trr_b,
        "overall_trr":          overall,
        "verdict_disease_a":    verdict_a,
        "verdict_disease_b":    verdict_b,
        "overall_verdict":      overall_verdict,
        "day1_severity_a":      day1_sev_a,
        "day7_severity_a":      day7_sev_a,
        "day1_severity_b":      day1_sev_b,
        "day7_severity_b":      day7_sev_b,
        "weather_caused_failure": weather_caused_failure,
        "action":               _get_action(overall_verdict,
                                            weather_caused_failure)
    }

    return result


def _get_action(verdict: str, weather_caused: bool) -> str:
    if verdict == "SUCCESS":
        return (
            "Treatment is working. Continue current treatment. "
            "Monitor for re-emergence if humidity rises."
        )
    elif verdict == "PARTIAL":
        return (
            "Treatment partially effective. "
            "Extend treatment for 3 more days. "
            "Re-evaluate conditions."
        )
    else:  # FAILURE
        if weather_caused:
            return (
                "Treatment failed possibly due to weather conditions. "
                "Heavy rainfall may have washed away fungicide. "
                "Alternative treatment recommended."
            )
        return (
            "Treatment failed. "
            "Disease not responding to current medicine. "
            "Alternative treatment recommended via RAG engine."
        )