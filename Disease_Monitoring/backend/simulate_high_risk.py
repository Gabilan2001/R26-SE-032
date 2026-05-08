"""
Simulation: High Risk Disease & Weather Scenario
This script simulates a "Worst Case" response to show all High Risk Alerts.
"""
import json

# ── Mocking a HIGH RISK Scenario ──
# 1. High Disease Severity (65%)
# 2. High Weather Risk (95% Humidity + Heavy Rain)
# 3. Worsening Status (Day 3 severity is higher than Day 1)

mock_response = {
    "session_id": "farmer_test_999",
    "day": 3,
    "image_valid": True,
    "rejection_reason": None,
    "disease_a_severity": 65.2,
    "disease_b_severity": 10.5,
    "disease_a_confidence": 0.88,
    "disease_b_confidence": 0.72,
    
    # ── COMBINED RISK (The system's final verdict) ──
    "combined_risk_score": 82.4,
    "combined_risk_level": "HIGH", 
    
    # ── WEATHER ALERTS (From Weather API) ──
    "weather_risk_score": 92.0,
    "weather_risk_level": "HIGH",
    "weather_alert": "High fungal risk! Humidity 95%, Rainfall 15mm. Treatment may wash away. Consider re-spraying after weather improves.",
    
    # ── MONITORING ALERTS (From Rule Engine) ──
    "daily_status": "PROGRESS_MONITORED",
    "daily_alerts": [
        "CRITICAL: Treatment is NOT stopping the disease. Infection is spreading or stagnant. Check application method.",
        "Heavy rainfall (15mm) detected. Contact fungicide may wash away. Consider systemic fungicide.",
        "Weather risk is HIGH. Current slow recovery is likely due to high humidity/rain assisting disease spread."
    ],
    
    # ── TREATMENT ADVICE (From RAG Engine) ──
    "treatment_advice": {
        "medicine_name": "Mancozeb 75WP",
        "chemical_class": "Dithiocarbamate",
        "type": "Systemic",
        "dosage": "2g/L water",
        "rain_advice": "Apply in dry period. This medicine absorbs into leaf tissue and is rain resistant.",
        "reason": "Alternative to failed treatment. Different chemical class prevents resistance. Suitable for Early_Blight."
    }
}

print("="*60)
print("     SIMULATED HIGH-RISK API RESPONSE")
print("="*60)
print(json.dumps(mock_response, indent=2))
print("="*60)
print("\nALERTS SUMMARY:")
print(f"OVERALL VERDICT: {mock_response['combined_risk_level']}")
print(f"WEATHER WARNING: {mock_response['weather_alert']}")
print("-" * 30)
for alert in mock_response['daily_alerts']:
    print(f"ALERT: {alert}")
print("="*60)
