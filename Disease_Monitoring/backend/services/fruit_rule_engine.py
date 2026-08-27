"""
Fruit Rule Engine
Handles multi-day monitoring logic for tomato fruit diseases.
"""

def compute_fruit_daily_output(day: int, 
                               sev_anth: float,
                               sev_ber: float,
                               sev_swv: float,
                               weather: dict,
                               prev_anth: float = None,
                               prev_ber: float = None,
                               prev_swv: float = None) -> dict:
    """
    Calculates combined risk and monitoring status for fruit diseases.
    """
    risk_score = weather.get("risk_score", 0)
    risk_level = weather.get("risk_level", "UNKNOWN")
    
    # ── Combined Risk Assessment ──────────────────────────────────────────────
    # Formula: (Max Severity * 0.6) + (Weather Risk * 0.4)
    max_sev = max(sev_anth, sev_ber, sev_swv)
    combined_score = round((max_sev * 0.6) + (risk_score * 0.4), 2)
    
    if max_sev > 50 or combined_score > 60:
        combined_level = "HIGH"
    elif combined_score > 25:
        combined_level = "MEDIUM"
    else:
        combined_level = "LOW"

    result = {
        "day":                  day,
        "anth_severity":        sev_anth,
        "ber_severity":         sev_ber,
        "swv_severity":         sev_swv,
        "combined_risk_score":  combined_score,
        "combined_risk_level":  combined_level,
        "alerts":               []
    }

    # Progression Analysis (Day 3)
    if day == 3:
        def check_status(curr, prev):
            if prev is None: return "NEW"
            drop = prev - curr
            if drop > 0: return "ON_TRACK" if (drop/2) >= 1.0 else "SLOW_RECOVERY"
            return "WORSENING" if drop < 0 else "STAGNANT"

        status_anth = check_status(sev_anth, prev_anth)
        status_ber  = check_status(sev_ber, prev_ber)
        status_swv  = check_status(sev_swv, prev_swv)
        
        result["status_anthracnose"] = status_anth
        result["status_blossom_end_rot"] = status_ber
        result["status_spotted_wilt_virus"] = status_swv

        if any(s in ["WORSENING", "STAGNANT"] for s in [status_anth, status_ber, status_swv]):
            result["alerts"].append("CRITICAL: One or more diseases are not responding to treatment.")
        else:
            result["alerts"].append("Progressing well.")

    result["status"] = "BASELINE" if day == 1 else "MONITORED"
    return result
