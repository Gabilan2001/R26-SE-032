"""
Verification Script for Seasonal Planning Forecast Endpoint.
Tests the 3 required scenarios:
1. Dambulla-Wholesale, December 2026
2. Dambulla-Wholesale, October 2026
3. Pettah-Retail, May 2027
"""

from pathlib import Path
import os
import sys
import json
import urllib.request

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.seasonal_service import get_seasonal_planning_forecast

TEST_CASES = [
    {"market": "Dambulla", "type": "Wholesale", "target_month": 12, "target_year": 2026, "label": "Dambulla-Wholesale, December 2026"},
    {"market": "Dambulla", "type": "Wholesale", "target_month": 10, "target_year": 2026, "label": "Dambulla-Wholesale, October 2026"},
    {"market": "Pettah", "type": "Retail", "target_month": 5, "target_year": 2027, "label": "Pettah-Retail, May 2027"},
]

def test_seasonal_requests():
    print("==================================================================================")
    print(" VERIFICATION: 3 REAL SEASONAL PLANNING ENDPOINT REQUESTS")
    print("==================================================================================\n")

    for idx, tc in enumerate(TEST_CASES, 1):
        print(f"TEST CASE {idx}: {tc['label']}")
        print("----------------------------------------------------------------------------------")
        
        # 1. Direct Service Call
        res = get_seasonal_planning_forecast(
            market=tc["market"],
            series_type=tc["type"],
            target_month=tc["target_month"],
            target_year=tc["target_year"],
        )
        print(json.dumps(res, indent=2))
        print("\n" + "="*82 + "\n")

if __name__ == "__main__":
    test_seasonal_requests()
