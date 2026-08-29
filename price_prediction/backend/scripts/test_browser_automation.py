"""
Test browser automation availability (Playwright / Selenium / urllib / Chrome remote).
"""

import sys

def test_imports():
    print("Testing Playwright import...")
    try:
        from playwright.sync_api import sync_playwright
        print("  Playwright is INSTALLED!")
        return "playwright"
    except ImportError:
        print("  Playwright NOT installed.")

    print("Testing Selenium import...")
    try:
        from selenium import webdriver
        print("  Selenium is INSTALLED!")
        return "selenium"
    except ImportError:
        print("  Selenium NOT installed.")

    return None

if __name__ == "__main__":
    test_imports()
