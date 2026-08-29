"""
Live Headless Browser Verification Script using Playwright.
Navigates to http://127.0.0.1:8000/ui/, selects 'Dambulla - Wholesale',
waits for DOM render, verifies #weather-body content, and captures a screenshot.
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import time

ARTIFACT_DIR = Path(r"C:\Users\Rashad's_HP\.gemini\antigravity-ide\brain\67386d21-ac9f-4464-8c10-9bbb654b0d5a")

def run_browser_verification():
    print("==================================================================================")
    print(" LIVE BROWSER RUNTIME VERIFICATION (PLAYWRIGHT)")
    print("==================================================================================\n")

    with sync_playwright() as p:
        # Launch using system installed Edge/Chrome on Windows
        try:
            browser = p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})

        page = context.new_page()

        # Track network requests
        network_logs = []
        page.on("request", lambda req: network_logs.append(f"REQ: {req.method} {req.url}"))
        page.on("response", lambda res: network_logs.append(f"RESP: {res.status} {res.url}"))

        # Track console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"CONSOLE {msg.type}: {msg.text}"))

        print("1. Navigating to http://127.0.0.1:8000/ui/...")
        page.goto("http://127.0.0.1:8000/ui/?v=3", wait_until="domcontentloaded")


        # Select 'Dambulla - Wholesale' from market-select
        print("2. Selecting 'Dambulla - Wholesale' in market-select dropdown...")
        page.select_option("#market-select", "Dambulla-Wholesale")

        # Wait 3 seconds for POST /predict/ response and DOM render
        time.sleep(3)

        # Inspect #weather-body text
        weather_text = page.inner_text("#weather-body")
        print(f"\n3. Browser Render Verification Results:")
        print(f"   - Is #weather-section visible? -> {page.is_visible('#weather-section')}")
        print(f"   - Does #weather-body contain 'Sri Lankan Tomato Supply Weather Impact'? -> {'Sri Lankan Tomato Supply Weather Impact' in weather_text}")
        print(f"   - Does #weather-body contain 'Growing Region Weather (Anuradhapura)'? -> {'Growing Region Weather (Anuradhapura)' in weather_text}")
        print(f"   - Are all 4 stations present? -> {all(st in weather_text for st in ['Anuradhapura', 'Badulla', 'Dambulla', 'Nuwara Eliya'])}")
        print(f"   - Stations found in text: {[st for st in ['Anuradhapura', 'Badulla', 'Dambulla', 'Nuwara Eliya'] if st in weather_text]}")

        # Inspect #news-body text
        news_text = page.inner_text("#news-body")
        print(f"\n4. News Card Verification Results:")
        print(f"   - Is #news-section visible? -> {page.is_visible('#news-section')}")
        print(f"   - Does #news-body contain 'Greetings from a wildlife park'? -> {'Greetings from a wildlife park' in news_text}")
        print(f"   - Does #news-body contain 'No major supply alerts reported in recent news monitoring'? -> {'No major supply alerts reported in recent news monitoring' in news_text}")

        print(f"   - Contains 21d Rain: {'21d Rain' in weather_text}")
        print(f"   - Contains Market Storage Impact: {'Market Storage Impact' in weather_text}")

        # Filter POST /predict/ requests
        predict_reqs = [l for l in network_logs if "/predict/" in l]
        print(f"\n5. Network Requests Log for /predict/:")
        for r in predict_reqs:
            print(f"   {r}")

        # Check console errors
        errors = [c for c in console_logs if "error" in c.lower()]
        print(f"\n5. Browser Console Errors ({len(errors)}):")
        for e in errors:
            print(f"   {e}")

        # Capture Screenshot
        screenshot_path = ARTIFACT_DIR / "browser_verification_fixed_weather_ui.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n6. Screenshot captured and saved to: {screenshot_path}")

        # Click 'Generate AI Selling Forecast' and wait for forecast result to be visible
        print("\n7. Clicking 'Generate AI Selling Forecast' button...")
        page.click("#btn-forecast")
        
        # Wait up to 20s for TensorFlow BiLSTM models to finish and render forecast result
        page.wait_for_selector("#forecast-result:not([hidden])", timeout=25000)
        time.sleep(1)

        weather_body_text = page.inner_text("#weather-body")
        print(f"\n8. Post-Forecast Browser Render Verification:")
        print(f"   - Is #weather-section visible? -> {page.is_visible('#weather-section')}")
        print(f"   - Does #weather-body contain 'Sri Lankan Tomato Supply Weather Impact'? -> {'Sri Lankan Tomato Supply Weather Impact' in weather_body_text}")
        print(f"   - Does #weather-body contain 'Growing Region Weather (Anuradhapura)'? -> {'Growing Region Weather (Anuradhapura)' in weather_body_text}")
        print(f"   - Are all 4 stations present in sidebar? -> {all(st in weather_body_text for st in ['Anuradhapura', 'Badulla', 'Dambulla', 'Nuwara Eliya'])}")
        print(f"   - Stations found in sidebar: {[st for st in ['Anuradhapura', 'Badulla', 'Dambulla', 'Nuwara Eliya'] if st in weather_body_text]}")
        print(f"   - Contains 21d Rain: {'21d Rain' in weather_body_text}")
        print(f"   - Contains Market Storage Impact: {'Market Storage Impact' in weather_body_text}")

        forecast_result_text = page.inner_text("#forecast-result")
        has_dup_in_forecast = "Sri Lankan Tomato Supply Weather Impact" in forecast_result_text
        print(f"   - Does #forecast-result contain a duplicate regional weather card? -> {has_dup_in_forecast}")

        # Capture post-forecast screenshot
        post_forecast_shot = ARTIFACT_DIR / "browser_post_forecast_result.png"
        page.screenshot(path=str(post_forecast_shot), full_page=True)
        print(f"   - Post-forecast screenshot saved to: {post_forecast_shot}")


        browser.close()

if __name__ == "__main__":
    run_browser_verification()
