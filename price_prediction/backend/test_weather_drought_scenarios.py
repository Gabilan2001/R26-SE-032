"""
Comprehensive Test Script for Drought, Water Availability, and Agricultural Weather Impact Analysis.
Tests Scenarios A, B, C, D, E as required in the specification.
"""

import sys
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.weather_service import _classify_weather
from app.services.regional_weather_service import RegionalWeatherService
from app.services.news_event_service import _rule_based_classify_article, _analyze_article_patterns
from app.services.news_impact_service import _extract_agricultural_records
from app.services.decision_engine_service import get_full_recommendation


def test_scenario_a():
    """Scenario A — Normal conditions: Moderate rainfall (10mm) + normal temperature (26°C)."""
    print("\n" + "="*80)
    print("TEST SCENARIO A: Normal Balanced Conditions")
    print("="*80)
    dates = [f"2026-03-{i:02d}" for i in range(1, 8)]
    rains = [8.0, 12.0, 5.0, 10.0, 7.0, 6.0, 9.0]
    temps = [26.0, 26.5, 25.8, 26.2, 27.0, 26.1, 26.4]
    hums = [75.0] * 7

    res = _classify_weather("Dambulla", dates, rains, temps, hums)
    signal, storm_risk, score, price_effect, reason, impact, max_r, avg_t, avg_h, w_stress, h_stress, fav, agri_impact = res

    print(f"Weather Signal       : {signal}")
    print(f"Water Stress Level   : {w_stress}")
    print(f"Heat Stress Level    : {h_stress}")
    print(f"Favourability        : {fav}")
    print(f"Price Effect         : {price_effect}")
    print(f"Agricultural Stress  : {agri_impact['agricultural_stress']}")
    print(f"Tomato Supply Risk   : {agri_impact['tomato_supply_risk']}")
    print(f"Time Horizon         : {agri_impact['time_horizon']}")
    print(f"Reason               : {reason}")

    assert fav == "FAVOURABLE", f"Expected FAVOURABLE, got {fav}"
    assert w_stress == "NORMAL", f"Expected NORMAL, got {w_stress}"
    assert price_effect == "STABLE", f"Expected STABLE, got {price_effect}"
    print(">>> SCENARIO A PASSED SUCCESSFULLY! [OK]")


def test_scenario_b():
    """Scenario B — Heavy Rain: Extreme rainfall (65mm) + high wetness."""
    print("\n" + "="*80)
    print("TEST SCENARIO B: Heavy Rain / Flood Risk")
    print("="*80)
    dates = [f"2026-03-{i:02d}" for i in range(1, 8)]
    rains = [25.0, 65.0, 45.0, 30.0, 15.0, 10.0, 5.0]
    temps = [24.0] * 7
    hums = [92.0] * 7

    res = _classify_weather("Nuwara Eliya", dates, rains, temps, hums)
    signal, storm_risk, score, price_effect, reason, impact, max_r, avg_t, avg_h, w_stress, h_stress, fav, agri_impact = res

    print(f"Weather Signal       : {signal}")
    print(f"Water Stress Level   : {w_stress}")
    print(f"Price Effect         : {price_effect}")
    print(f"Tomato Supply Risk   : {agri_impact['tomato_supply_risk']}")
    print(f"Time Horizon         : {agri_impact['time_horizon']}")
    print(f"Reason               : {reason}")

    assert "flood" in signal or "heavy_rain" in signal, f"Expected heavy rain/flood signal, got {signal}"
    assert w_stress == "EXCESS_WATER", f"Expected EXCESS_WATER, got {w_stress}"
    assert price_effect == "UP", f"Expected UP, got {price_effect}"
    assert "Immediate" in agri_impact['time_horizon'] or "Short-term" in agri_impact['time_horizon']
    print(">>> SCENARIO B PASSED SUCCESSFULLY! [OK]")


def test_scenario_c():
    """Scenario C — Mild dry period: Low rainfall for 5 days (<0.05mm) with moderate temp (27°C)."""
    print("\n" + "="*80)
    print("TEST SCENARIO C: Mild Dry Period (Non-Alarmist)")
    print("="*80)
    dates = [f"2026-03-{i:02d}" for i in range(1, 6)]
    rains = [0.0, 0.0, 0.0, 0.0, 0.0]
    temps = [26.5, 27.0, 27.2, 26.8, 27.0]
    hums = [68.0] * 5

    res = _classify_weather("Anuradhapura", dates, rains, temps, hums)
    signal, storm_risk, score, price_effect, reason, impact, max_r, avg_t, avg_h, w_stress, h_stress, fav, agri_impact = res

    print(f"Weather Signal       : {signal}")
    print(f"Water Stress Level   : {w_stress}")
    print(f"Heat Stress Level    : {h_stress}")
    print(f"Favourability        : {fav}")
    print(f"Price Effect         : {price_effect}")
    print(f"Reason               : {reason}")

    assert fav == "FAVOURABLE" or signal == "favourable_dry", f"Expected favourable_dry, got {signal}"
    assert price_effect == "STABLE", f"Expected STABLE, got {price_effect}"
    assert w_stress == "NORMAL", f"Expected NORMAL for mild dry spell, got {w_stress}"
    print(">>> SCENARIO C PASSED SUCCESSFULLY! [OK] (Did NOT falsely classify mild dry spell as severe drought)")


def test_scenario_d():
    """Scenario D — Severe drought: Persistent dry spell + extreme heat (38°C)."""
    print("\n" + "="*80)
    print("TEST SCENARIO D: Severe Drought & Extreme Heat")
    print("="*80)
    dates = [f"2026-03-{i:02d}" for i in range(1, 15)]
    rains = [0.0] * 14
    temps = [36.5, 37.0, 38.2, 39.0, 38.5, 37.8, 38.0, 39.1, 38.4, 37.9, 38.2, 38.5, 37.0, 36.8]
    hums = [42.0] * 14

    res = _classify_weather("Anuradhapura", dates, rains, temps, hums)
    signal, storm_risk, score, price_effect, reason, impact, max_r, avg_t, avg_h, w_stress, h_stress, fav, agri_impact = res

    print(f"Weather Signal       : {signal}")
    print(f"Water Stress Level   : {w_stress}")
    print(f"Heat Stress Level    : {h_stress}")
    print(f"Favourability        : {fav}")
    print(f"Price Effect         : {price_effect}")
    print(f"Agricultural Stress  : {agri_impact['agricultural_stress']}")
    print(f"Tomato Supply Risk   : {agri_impact['tomato_supply_risk']}")
    print(f"Time Horizon         : {agri_impact['time_horizon']}")
    print(f"Reason               : {reason}")

    assert w_stress == "SEVERE_DROUGHT", f"Expected SEVERE_DROUGHT, got {w_stress}"
    assert h_stress == "EXTREME_HEAT", f"Expected EXTREME_HEAT, got {h_stress}"
    assert "Medium to Long-term" in agri_impact['time_horizon'], f"Expected medium/long-term horizon, got {agri_impact['time_horizon']}"
    print(">>> SCENARIO D PASSED SUCCESSFULLY! [OK]")


def test_scenario_e():
    """Scenario E — Real-World Test Case: August 16, 2026 Adaderana news article."""
    print("\n" + "="*80)
    print("TEST SCENARIO E: August 16, 2026 Adaderana News Analysis")
    print("="*80)

    adaderana_article = {
        "title": "Severe drought and extreme heat hit several districts",
        "description": (
            "Anuradhapura experiencing a prolonged dry spell. Temperatures expected around 39°C–45°C "
            "in several districts. Some areas going nearly four months without rain, small tanks completely drying up, "
            "severe water difficulties with residents using groundwater. Agricultural cultivation being damaged because of lack of water."
        ),
        "source": "Adaderana News",
        "url": "https://adaderana.lk/news/2026-08-16/drought-anuradhapura",
    }

    # 1. Test Rule-based Event Classifier
    patterns = _analyze_article_patterns(f"{adaderana_article['title']} {adaderana_article['description']}")
    classification = _rule_based_classify_article(adaderana_article, patterns=patterns)

    print("--- Event Classifier Output ---")
    print(f"Relevant             : {classification['relevant']}")
    print(f"Event Type           : {classification['event_type']}")
    print(f"Region Extracted     : {classification['region']}")
    print(f"Expected Direction   : {classification['expected_direction']}")
    print(f"Evidence Type        : {classification['evidence_type']}")
    print(f"Time Horizon         : {classification['time_horizon']}")
    print(f"Reason               : {classification['reason']}")

    record = classification["agricultural_impact_record"]
    print("\n--- Structured Agricultural Impact Record (Section 8) ---")
    print(json.dumps(record, indent=2))

    assert classification["relevant"] is True
    assert classification["event_type"] == "drought_water_stress"
    assert classification["region"] == "Anuradhapura"
    assert classification["evidence_type"] == "Indirect agricultural evidence", (
        f"Expected Indirect agricultural evidence (paddy/general cultivation/tanks), got {classification['evidence_type']}"
    )
    assert record["tomato_supply_risk"] == "Potential future risk", (
        f"Expected 'Potential future risk' without claiming direct immediate tomato loss, got {record['tomato_supply_risk']}"
    )
    assert "Medium/long term" in record["time_horizon"]
    print(">>> SCENARIO E PASSED SUCCESSFULLY! [OK]")


def test_decision_engine_end_to_end():
    """Test full decision engine with multi-station weather and news corroboration."""
    print("\n" + "="*80)
    print("TEST FULL DECISION ENGINE & REGIONAL WEATHER INTEGRATION")
    print("="*80)

    res = get_full_recommendation(
        market="Dambulla",
        series_type="Retail",
        target_date_str="2026-03-10",
        horizon_days=14,
    )

    print(f"Series               : {res['series']}")
    print(f"Current Price        : {res['current_price_lkr']:.2f} LKR/kg")
    print(f"Recommendation       : {res['recommendation']}")
    print(f"Action Code          : {res['action_code']}")
    print(f"Day 1 Forecast       : {res['day1_forecast_lkr']:.2f} LKR/kg")
    print(f"Day 14 Forecast      : {res['day14_forecast_lkr']:.2f} LKR/kg")
    print(f"Corroborated Signals : {res.get('corroborated_signals')}")

    reg = res.get("regional_weather_impact", {})
    struct_agri = reg.get("structured_agricultural_assessment", {})
    print("\n--- Regional Structured Agricultural Assessment ---")
    print(json.dumps(struct_agri, indent=2))

    assert "structured_agricultural_assessment" in reg
    assert "corroborated_signals" in res
    print(">>> DECISION ENGINE VERIFICATION PASSED! [OK]")


if __name__ == "__main__":
    test_scenario_a()
    test_scenario_b()
    test_scenario_c()
    test_scenario_d()
    test_scenario_e()
    test_decision_engine_end_to_end()
    print("\n" + "*"*80)
    print("ALL 5 SCENARIOS AND DECISION ENGINE INTEGRATION VERIFIED SUCCESSFULLY!")
    print("*"*80)
