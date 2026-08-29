"""
Live API Prediction Service Test.
Calls get_full_recommendation directly and verifies payload structure.
"""

from pathlib import Path
import sys
import json

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.decision_engine_service import get_full_recommendation

def test_live_recommendation():
    print("==================================================================================")
    print(" TESTING LIVE DECISION ENGINE WITH REGIONAL WEATHER IMPACT")
    print("==================================================================================\n")

    res = get_full_recommendation(market="Dambulla", series_type="Wholesale", target_date_str="2026-03-10")

    print("Success! Return Payload Summary:")
    print(f"  Series: {res['series']}")
    print(f"  Current Price: {res['current_price_lkr']} LKR/kg")
    print(f"  Day 1 Forecast: {res['day1_forecast_lkr']} LKR/kg")
    print(f"  Day 14 Forecast: {res['day14_forecast_lkr']} LKR/kg")
    print(f"  Recommendation: {res['recommendation']}")

    reg_impact = res.get("regional_weather_impact")
    if reg_impact:
        print("\n  Regional Weather Impact Payload:")
        print(f"    Season: {reg_impact['season']}")
        print(f"    Overall Risk: {reg_impact['overall_weather_risk']}")
        print(f"    Primary Region: {reg_impact['primary_region']}")
        print(f"    Primary Signal: {reg_impact['primary_signal']}")
        print(f"    Regions Audited: {list(reg_impact['growing_region_weather']['regions'].keys())}")
        print(f"    Market Storage Spoilage Risk: {reg_impact['market_storage_impact']['spoilage_risk_level']}")
    else:
        print("ERROR: regional_weather_impact missing!")

if __name__ == "__main__":
    test_live_recommendation()
