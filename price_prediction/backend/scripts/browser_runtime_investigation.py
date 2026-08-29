"""
READ-ONLY Browser Runtime Investigation Script.
Checks if playwright/selenium is available or uses python HTTP client to inspect live JS/HTML served by FastAPI.
Also inspects all files in frontend/ directory to check for multiple JS files, inline scripts in index.html, etc.
"""

from pathlib import Path
import json
import urllib.request
import re

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = (BASE_DIR / "../frontend").resolve()

def check_frontend_files():
    print("==================================================================================")
    print(" 1. FRONTEND DIRECTORY FILE INVENTORY")
    print("==================================================================================\n")

    print(f"Frontend Directory: {FRONTEND_DIR}")
    for p in FRONTEND_DIR.glob("*"):
        print(f"  - {p.name} (Size: {p.stat().st_size} bytes)")

def check_served_assets():
    print("\n==================================================================================")
    print(" 2. LIVE SERVED ASSETS FROM HTTP://127.0.0.1:8000/ui/")
    print("==================================================================================\n")

    # Fetch /ui/
    with urllib.request.urlopen("http://127.0.0.1:8000/ui/") as resp:
        html = resp.read().decode("utf-8")
        print("HTML Served at /ui/:")
        script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
        print(f"  Script tags found: {script_srcs}")
        
        # Check inline scripts in HTML
        inline_scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
        print(f"  Inline script blocks: {len(inline_scripts)}")
        for idx, sc in enumerate(inline_scripts):
            print(f"    Script {idx}: {sc[:100]}...")

    # Fetch /ui/app.js
    with urllib.request.urlopen("http://127.0.0.1:8000/ui/app.js") as resp:
        js = resp.read().decode("utf-8")
        print("\nJavaScript served at /ui/app.js:")
        print(f"  Length: {len(js)} bytes")
        
        # Check for multiple definitions of key functions
        for fn in ["renderWeatherCard", "buildRegionalWeatherCard", "onMarketChanged", "renderForecast"]:
            matches = list(re.finditer(rf'function\s+{fn}\s*\(', js))
            print(f"  Function '{fn}' count in app.js: {len(matches)} at character positions {[m.start() for m in matches]}")

        # Search for old Anuradhapura text string
        old_anura_strs = [line.strip() for line in js.splitlines() if "Anuradhapura" in line]
        print(f"  Anuradhapura text occurrences in served app.js: {len(old_anura_strs)}")
        for s in old_anura_strs:
            print(f"    - {s[:100]}")

if __name__ == "__main__":
    check_frontend_files()
    check_served_assets()
