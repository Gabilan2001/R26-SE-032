"""
Live News API Debug Script.
Calls NewsAPI.org and NewsData.io directly, prints raw API response,
and inspects the relevance filtering logic.
"""

from pathlib import Path
import os
import sys
import json
import dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load .env file
dotenv.load_dotenv(BASE_DIR / ".env")

from app.services.news_service import fetch_raw_articles_for_queries
from app.services.news_impact_service import analyze_agriculture_news_for_location, _RELEVANCE_PATTERN
from app.services.news_event_service import get_news_flag, _CACHE

def test_live_news_calls():
    print("==================================================================================")
    print(" LIVE NEWS API DEBUG & RELEVANCE FILTER TEST")
    print("==================================================================================\n")

    news_api_key = os.getenv("NEWS_API_KEY", "")
    newsdata_api_key = os.getenv("NEWSDATA_API_KEY", "")
    print(f"NEWS_API_KEY present: {bool(news_api_key)} (Starts with: '{news_api_key[:6]}...')")
    print(f"NEWSDATA_API_KEY present: {bool(newsdata_api_key)} (Starts with: '{newsdata_api_key[:6]}...')\n")

    # 1. Test raw articles fetched for queries
    queries = [
        "Sri Lanka agriculture Dambulla",
        "Sri Lanka vegetable market Dambulla",
        "Sri Lanka tomato crop Dambulla",
        "Sri Lanka food inflation Dambulla",
        "Sri Lanka vegetable price",
        "Sri Lanka agriculture",
        "tomato price Asia",
    ]

    articles, winning = fetch_raw_articles_for_queries(queries)
    print(f"Winning query: '{winning}'")
    print(f"Total raw articles fetched: {len(articles)}\n")

    print("RAW ARTICLES FETCHED:")
    for idx, art in enumerate(articles[:10], 1):
        title = art.get("title", "")
        desc = art.get("description", "")
        blob = f"{title} {desc}".lower()
        matched = bool(_RELEVANCE_PATTERN.search(blob))
        print(f"  {idx}. Title: {title}")
        print(f"     Description: {desc[:120]}...")
        print(f"     Passed _RELEVANCE_PATTERN? -> {matched}\n")

    # 2. Test analyze_agriculture_news_for_location
    print("----------------------------------------------------------------------------------")
    print("ANALYSIS RESULT FROM analyze_agriculture_news_for_location('Dambulla'):")
    res = analyze_agriculture_news_for_location("Dambulla")
    print(f"  Direction: {res.price_impact_direction}")
    print(f"  Sentiment: {res.news_sentiment}")
    print(f"  Headlines Count: {len(res.relevant_headlines)}")
    print("  Relevant Headlines:")
    for h in res.relevant_headlines:
        print(f"    - {h}")

    # 3. Test get_news_flag cache
    print("\n----------------------------------------------------------------------------------")
    print(f"_CACHE status in news_event_service: ts={_CACHE.get('timestamp')}, data_keys={list(_CACHE.get('data', {}).keys()) if _CACHE.get('data') else None}")

if __name__ == "__main__":
    test_live_news_calls()
