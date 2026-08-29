"""
Playwright Live Browser Test for Seasonal Planning Feature UI.
Navigates to http://127.0.0.1:8000/ui/, selects 'Target Selling Date',
chooses November 15, 2026 (>14 days horizon), clicks 'Generate AI Selling Forecast',
and verifies the rendered Seasonal Price Outlook card.
"""

from pathlib import Path
import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = Path(r"C:\Users\Rashad's_HP\.gemini\antigravity-ide\brain\67386d21-ac9f-4464-8c10-9bbb654b0d5a")

def run_seasonal_browser_test():
    print("==================================================================================")
    print(" LIVE BROWSER VERIFICATION FOR SEASONAL PLANNING MODE (PLAYWRIGHT)")
    print("==================================================================================\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="msedge")
        page = browser.new_page()

        print("1. Navigating to http://127.0.0.1:8000/ui/...")
        page.goto("http://127.0.0.1:8000/ui/", wait_until="domcontentloaded")
        time.sleep(2)

        print("2. Selecting 'Dambulla - Wholesale' in market-select dropdown...")
        page.select_option("#market-select", "Dambulla-Wholesale")
        time.sleep(2)

        print("3. Switching forecast mode to 'Target Selling Date'...")
        page.click("input[value='date']")
        time.sleep(1)

        print("4. Entering target date '2026-11-15' (> 14 days horizon)...")
        page.fill("#target-date", "2026-11-15")
        time.sleep(1)

        print("5. Clicking 'Generate AI Selling Forecast' button...")
        page.click("#btn-forecast")
        
        # Wait up to 10s for seasonal endpoint API and DOM render
        page.wait_for_selector("#forecast-result:not([hidden])", timeout=10000)
        time.sleep(2)

        forecast_text = page.inner_text("#forecast-result")
        print("\n6. Seasonal Planning UI Verification Results:")
        print(f"   - Is #forecast-result visible? -> {page.is_visible('#forecast-result')}")
        print(f"   - Contains 'Seasonal Price Outlook'? -> {'Seasonal Price Outlook' in forecast_text}")
        print(f"   - Contains 'MODERATE CONFIDENCE' or 'HIGH' or 'LOW'? -> {any(c in forecast_text for c in ['HIGH CONFIDENCE', 'MODERATE CONFIDENCE', 'LOW CONFIDENCE'])}")
        print(f"   - Contains 'Expected Seasonal Price Range'? -> {'Expected Seasonal Price Range' in forecast_text}")
        print(f"   - Contains 'This is a planning estimate, not a precise forecast'? -> {'This is a planning estimate, not a precise forecast' in forecast_text}")

        # Capture screenshot
        shot_path = ARTIFACT_DIR / "browser_seasonal_planning_ui.png"
        page.screenshot(path=str(shot_path), full_page=True)
        print(f"   - Screenshot saved to: {shot_path}")

        browser.close()

if __name__ == "__main__":
    run_seasonal_browser_test()
