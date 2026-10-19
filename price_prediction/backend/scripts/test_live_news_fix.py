"""
Live News Fix Verification Script.
Calls analyze_agriculture_news_for_location('Dambulla') and GET /news/market-analysis
to verify fresh, strictly relevant news response or honest fallback state.
"""

from pathlib import Path
import os
import sys
import json
import urllib.request
import dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
dotenv.load_dotenv(BASE_DIR / ".env")

from app.services.news_impact_service import analyze_agriculture_news_for_location

def test_live_news_fix():
    print("==================================================================================")
    print(" LIVE VERIFICATION OF NEWS IMPACT SERVICE & RELEVANCE FILTER")
    print("==================================================================================\n")

    # 1. Direct Python call to analyze_agriculture_news_for_location
    print("1. Direct Python Call: analyze_agriculture_news_for_location('Dambulla'):")
    res = analyze_agriculture_news_for_location("Dambulla")
    print(f"   Price Impact Direction: {res.price_impact_direction}")
    print(f"   News Sentiment: {res.news_sentiment}")
    print(f"   Market Impact Summary: {res.market_impact_summary}")
    print(f"   Articles Analyzed: {res.articles_analyzed}")
    print(f"   Relevant Headlines ({len(res.relevant_headlines)}):")
    if res.relevant_headlines:
        for h in res.relevant_headlines:
            print(f"     - {h}")
    else:
        print("     (None — honest fallback message displayed cleanly!)")

    # 2. Live HTTP GET to http://127.0.0.1:8000/news/market-analysis?location=Dambulla
    print("\n----------------------------------------------------------------------------------")
    print("2. Live HTTP GET http://127.0.0.1:8000/news/market-analysis?location=Dambulla:")
    try:
        url = "http://127.0.0.1:8000/news/market-analysis?location=Dambulla"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"   HTTP Status: {resp.status}")
            print(f"   Response Payload Summary:")
            print(f"     news_sentiment: {data.get('news_sentiment')}")
            print(f"     market_impact_summary: {data.get('market_impact_summary')}")
            print(f"     relevant_headlines: {data.get('relevant_headlines')}")
            
            # Confirm irrelevant wildlife headline is NOT present
            has_wildlife = any("wildlife" in h.lower() or "elephant" in h.lower() for h in data.get("relevant_headlines", []))
            print(f"   Is irrelevant wildlife headline present? -> {has_wildlife} (Must be False!)")
    except Exception as e:
        print(f"   API Request Error: {e}")

if __name__ == "__main__":
    test_live_news_fix()
