"""
Test Runtime Bug: Verify GET /predict/ returns 405 vs POST /predict/ returns 200.
"""

import urllib.request
import urllib.error

def test_http_methods():
    print("==================================================================================")
    print(" TESTING HTTP METHODS ON /predict/")
    print("==================================================================================\n")

    # 1. Test GET /predict/ (what onMarketChanged() was sending)
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/predict/", method="GET")
        with urllib.request.urlopen(req) as resp:
            print(f"GET /predict/ status: {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"GET /predict/ returned HTTP {e.code} ({e.reason}) <-- THIS CAUSED THE FAILURE IN onMarketChanged()!")

    # 2. Test POST /predict/ (correct HTTP method)
    try:
        import json
        payload = json.dumps({"market": "Dambulla", "type": "Wholesale", "forecast_horizon_days": 14}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:8000/predict/", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            print(f"POST /predict/ status: {resp.status} OK!")
    except urllib.error.HTTPError as e:
        print(f"POST /predict/ error: {e.code}")

if __name__ == "__main__":
    test_http_methods()
