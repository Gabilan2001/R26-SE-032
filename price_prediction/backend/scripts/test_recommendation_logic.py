"""
Comprehensive Verification and Test Suite for Redesigned Selling Recommendation Logic.
Tests synthetic cases, real production cases, frontend mapping logic, and backward compatibility.
"""

from pathlib import Path
import sys
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.decision_engine_service import get_full_recommendation
from app.services.seasonal_service import get_seasonal_planning_forecast


def evaluate_trajectory_rules(P0: float, forecast: list[float], is_anomaly: bool = False, series_label: str = "Dambulla-Wholesale"):
    """Standalone evaluator applying the exact same rules as decision_engine_service.py for unit testing."""
    h_len = len(forecast)
    peak_price = float(np.max(forecast))
    peak_idx = int(np.argmax(forecast))
    peak_day = peak_idx + 1
    minimum_price = float(np.min(forecast))
    terminal_price = float(forecast[-1])

    peak_change_pct = ((peak_price - P0) / P0) * 100.0 if P0 > 0 else 0.0
    terminal_change_pct = ((terminal_price - P0) / P0) * 100.0 if P0 > 0 else 0.0
    post_peak_drop_pct = ((peak_price - terminal_price) / peak_price) * 100.0 if peak_price > 0 else 0.0

    if h_len > 1:
        x_vals = np.arange(1, h_len + 1)
        y_vals = np.array(forecast)
        x_mean = np.mean(x_vals)
        y_mean = np.mean(y_vals)
        slope = float(np.sum((x_vals - x_mean) * (y_vals - y_mean)) / np.sum((x_vals - x_mean) ** 2))
        slope_pct_per_day = (slope / P0) * 100.0 if P0 > 0 else 0.0
    else:
        slope = 0.0
        slope_pct_per_day = 0.0

    if slope_pct_per_day <= -0.30 or terminal_change_pct <= -3.5:
        trend = "DECLINING"
    elif slope_pct_per_day >= 0.30 or terminal_change_pct >= 3.5:
        trend = "RISING"
    else:
        trend = "STABLE"

    if is_anomaly:
        action_code = "MONITOR"
        recommendation = "MONITOR — Market Anomaly Detected"
        optimal_sell_day = 1
        optimal_sell_price_lkr = round(forecast[0], 2)
    elif peak_day <= 2 and (terminal_change_pct < 0 or post_peak_drop_pct >= 3.5):
        action_code = "SELL_NOW"
        recommendation = "SELL NOW — Peak Price in Next 1–2 Days"
        optimal_sell_day = peak_day
        optimal_sell_price_lkr = round(peak_price, 2)
    elif forecast[0] < P0 and terminal_change_pct <= -3.5 and peak_change_pct < 1.5:
        action_code = "SELL_NOW"
        recommendation = "SELL NOW — Prices Expected to Decline"
        optimal_sell_day = 1
        optimal_sell_price_lkr = round(forecast[0], 2)
    elif 3 <= peak_day <= 5 and peak_change_pct >= 3.5:
        action_code = "HOLD"
        recommendation = f"HOLD — Optimal Selling Window Around Day {peak_day}"
        optimal_sell_day = peak_day
        optimal_sell_price_lkr = round(peak_price, 2)
    elif peak_day > 5 and peak_change_pct >= 5.0:
        action_code = "HOLD"
        recommendation = f"HOLD — Higher Prices Projected Around Day {peak_day}"
        optimal_sell_day = peak_day
        optimal_sell_price_lkr = round(peak_price, 2)
    else:
        action_code = "STABLE"
        recommendation = "SELL NOW OR HOLD — Prices Expected to Stay Stable"
        optimal_sell_day = peak_day
        optimal_sell_price_lkr = round(peak_price, 2)

    return {
        "action_code": action_code,
        "recommendation": recommendation,
        "peak_price": round(peak_price, 2),
        "peak_day": peak_day,
        "terminal_price": round(terminal_price, 2),
        "peak_change_pct": round(peak_change_pct, 2),
        "terminal_change_pct": round(terminal_change_pct, 2),
        "post_peak_drop_pct": round(post_peak_drop_pct, 2),
        "trend": trend,
        "optimal_sell_day": optimal_sell_day,
        "optimal_sell_price_lkr": round(optimal_sell_price_lkr, 2),
    }


def run_tests():
    print("=" * 80)
    print(" TOMATO AI SELLING RECOMMENDATION LOGIC — TEST SUITE")
    print("=" * 80 + "\n")

    # -------------------------------------------------------------------------
    # TEST 1: Early Peak Followed by Decline
    # -------------------------------------------------------------------------
    print("[TEST 1] Early Peak Followed by Decline")
    p0_1 = 210.0
    f_1 = [222, 219, 216, 214, 211, 209, 207, 205, 203, 201, 199, 197, 196, 195]
    r1 = evaluate_trajectory_rules(p0_1, f_1)
    print(f"  - action_code: {r1['action_code']}")
    print(f"  - peak_day: {r1['peak_day']}")
    print(f"  - trend: {r1['trend']}")
    assert r1["action_code"] == "SELL_NOW", f"Test 1 failed! Expected SELL_NOW, got {r1['action_code']}"
    assert r1["peak_day"] == 1, f"Test 1 failed! Expected peak_day 1, got {r1['peak_day']}"
    assert r1["trend"] == "DECLINING", f"Test 1 failed! Expected DECLINING trend, got {r1['trend']}"
    print("  -> PASSED\n")

    # -------------------------------------------------------------------------
    # TEST 2: Mid-Term Peak on Day 4 (Safe holding window)
    # -------------------------------------------------------------------------
    print("[TEST 2] Mid-Term Peak on Day 4")
    p0_2 = 210.0
    f_2 = [212, 215, 220, 225, 221, 217, 214, 212, 210, 208, 207, 205, 204, 203]
    r2 = evaluate_trajectory_rules(p0_2, f_2)
    print(f"  - action_code: {r2['action_code']}")
    print(f"  - peak_day: {r2['peak_day']}")
    print(f"  - optimal_sell_day: {r2['optimal_sell_day']}")
    print(f"  - peak_price: {r2['peak_price']}")
    assert r2["action_code"] == "HOLD", f"Test 2 failed! Expected HOLD, got {r2['action_code']}"
    assert r2["peak_day"] == 4, f"Test 2 failed! Expected peak_day 4, got {r2['peak_day']}"
    print("  -> PASSED\n")

    # -------------------------------------------------------------------------
    # TEST 3: Continuous Decline Across Horizon
    # -------------------------------------------------------------------------
    print("[TEST 3] Continuous Downward Trend")
    p0_3 = 210.0
    f_3 = [205, 202, 199, 196, 193, 190, 188, 186, 184, 182, 180, 178, 176, 175]
    r3 = evaluate_trajectory_rules(p0_3, f_3)
    print(f"  - action_code: {r3['action_code']}")
    print(f"  - trend: {r3['trend']}")
    print(f"  - terminal_change_pct: {r3['terminal_change_pct']}%")
    assert r3["action_code"] == "SELL_NOW", f"Test 3 failed! Expected SELL_NOW, got {r3['action_code']}"
    assert r3["trend"] == "DECLINING", f"Test 3 failed! Expected DECLINING trend, got {r3['trend']}"
    print("  -> PASSED\n")

    # -------------------------------------------------------------------------
    # TEST 4: Stable Forecast (within +/- 3.5%)
    # -------------------------------------------------------------------------
    print("[TEST 4] Stable Trajectory")
    p0_4 = 210.0
    f_4 = [211, 210, 212, 211, 209, 210, 211, 210, 212, 211, 210, 209, 210, 211]
    r4 = evaluate_trajectory_rules(p0_4, f_4)
    print(f"  - action_code: {r4['action_code']}")
    print(f"  - peak_change_pct: {r4['peak_change_pct']}%")
    print(f"  - terminal_change_pct: {r4['terminal_change_pct']}%")
    assert r4["action_code"] == "STABLE", f"Test 4 failed! Expected STABLE, got {r4['action_code']}"
    print("  -> PASSED\n")

    # -------------------------------------------------------------------------
    # TEST 5: Market Anomaly Trigger (Highest Priority)
    # -------------------------------------------------------------------------
    print("[TEST 5] Market Anomaly Override")
    p0_5 = 210.0
    f_5 = [225, 230, 235, 240, 245, 250, 255, 260, 265, 270, 275, 280, 285, 290]
    r5 = evaluate_trajectory_rules(p0_5, f_5, is_anomaly=True)
    print(f"  - action_code: {r5['action_code']}")
    assert r5["action_code"] == "MONITOR", f"Test 5 failed! Expected MONITOR, got {r5['action_code']}"
    print("  -> PASSED\n")

    # -------------------------------------------------------------------------
    # TEST 6: Actual Production Problem Case
    # -------------------------------------------------------------------------
    print("[TEST 6] Actual Production Problem Case")
    p0_6 = 210.0
    f_6 = [222.46, 219.78, 217.36, 214.95, 211.86, 209.96, 208.12, 205.90, 204.09, 202.00, 200.17, 198.30, 196.46, 194.64]
    r6 = evaluate_trajectory_rules(p0_6, f_6)
    print(f"  - Current Observed: {p0_6} LKR")
    print(f"  - Day 1: {f_6[0]} LKR")
    print(f"  - Day 14: {f_6[-1]} LKR")
    print(f"  - action_code: {r6['action_code']}")
    print(f"  - recommendation: {r6['recommendation']}")
    print(f"  - peak_day: {r6['peak_day']}")
    print(f"  - peak_price: {r6['peak_price']} LKR ({r6['peak_change_pct']:+.2f}%)")
    print(f"  - terminal_price: {r6['terminal_price']} LKR ({r6['terminal_change_pct']:+.2f}%)")
    print(f"  - post_peak_drop: {r6['post_peak_drop_pct']:.2f}%")
    print(f"  - trend: {r6['trend']}")
    assert r6["action_code"] == "SELL_NOW", f"Test 6 failed! Expected SELL_NOW, got {r6['action_code']}"
    assert r6["peak_day"] == 1, f"Test 6 failed! Expected peak_day 1, got {r6['peak_day']}"
    assert r6["trend"] == "DECLINING", f"Test 6 failed! Expected DECLINING, got {r6['trend']}"
    assert "HOLD" not in r6["action_code"], "Test 6 failed! Action code must not be HOLD"
    print("  -> PASSED (Old contradiction successfully eliminated!)\n")

    # -------------------------------------------------------------------------
    # TEST 7: Frontend Action Code Resolution Simulation
    # -------------------------------------------------------------------------
    print("[TEST 7] Frontend Action Mapping & Ambiguity Prevention")
    def simulate_frontend_advice_copy(action_code, recommendation):
        code = str(action_code or "").upper()
        if code == "MONITOR" or "MONITOR" in recommendation.upper():
            return "banner-monitor"
        if code == "SELL_NOW":
            return "banner-sell"
        if code == "HOLD":
            return "banner-hold"
        return "banner-stable"

    banner_prod = simulate_frontend_advice_copy(r6["action_code"], r6["recommendation"])
    banner_stable = simulate_frontend_advice_copy("STABLE", "SELL NOW OR HOLD — Prices Expected to Stay Stable")
    print(f"  - Production Case Banner: {banner_prod}")
    print(f"  - Stable String Banner: {banner_stable}")
    assert banner_prod == "banner-sell", f"Expected banner-sell, got {banner_prod}"
    assert banner_stable == "banner-stable", f"Expected banner-stable, got {banner_stable}"
    print("  -> PASSED\n")

    # -------------------------------------------------------------------------
    # TEST 8: Live Service Execution & Backward Compatibility Verification
    # -------------------------------------------------------------------------
    print("[TEST 8] Live Service Execution & Model Preservation")
    live_res = get_full_recommendation("Dambulla", "Wholesale", target_date_str="2026-08-30", horizon_days=14)
    print(f"  - Live Action Code: {live_res['action_code']}")
    print(f"  - Live Recommendation: {live_res['recommendation']}")
    print(f"  - Live Peak Price: {live_res['peak_price_lkr']} LKR (Day {live_res['peak_day']})")
    print(f"  - Live Day 1 Forecast: {live_res['day1_forecast_lkr']} LKR")
    print(f"  - Live Day 14 Forecast: {live_res['day14_forecast_lkr']} LKR")
    print(f"  - Live Trajectory: {live_res['weather_adjusted_forecast']}")
    print(f"  - Live SHAP Available: {'shap_explanation' in live_res and live_res['shap_explanation'] is not None}")
    print(f"  - Live Anomaly Check Available: {'is_anomaly' in live_res}")
    
    # Confirm exact price numbers are preserved and valid
    assert abs(live_res["current_price_lkr"] - 210.0) < 0.01
    assert live_res["day1_forecast_lkr"] > 0
    assert live_res["day14_forecast_lkr"] > 0
    assert live_res["action_code"] == "SELL_NOW"
    assert live_res["peak_day"] == 1
    assert live_res["trend"] == "DECLINING"
    print("  -> PASSED\n")

    print("=" * 80)
    print(" ALL 8 TESTS PASSED SUCCESSFULLY! ")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
