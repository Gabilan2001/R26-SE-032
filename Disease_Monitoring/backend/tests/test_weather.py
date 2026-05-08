"""Quick test to verify weather API works"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from utils.weather_utils import get_weather_risk

# Test with Colombo, Sri Lanka coordinates
lat = 6.9271
lon = 79.8612

print("Testing Weather API...")
print(f"Location: Colombo, Sri Lanka ({lat}, {lon})")
print()

result = get_weather_risk(lat, lon)

print(f"Risk Score:  {result['risk_score']}")
print(f"Risk Level:  {result['risk_level']}")
print(f"Alert:       {result['alert']}")
print(f"City:        {result.get('city', 'N/A')}")
print()
print("Weather Details:")
for k, v in result['details'].items():
    print(f"  {k}: {v}")