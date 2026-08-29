"""
Test New Strict Relevance Filter and Honest Fallback Logic.
"""

from pathlib import Path
import os
import sys
import re

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import dotenv
dotenv.load_dotenv(BASE_DIR / ".env")

from app.services.news_service import fetch_raw_articles_for_queries

# Strict Agricultural & Market Relevance Pattern
_STRICT_AGRI_MARKET_PATTERN = re.compile(
    r"\b(tomato|tomatoes|vegetable|vegetables|crop|crops|harvest|harvests|farm|farmers|farming|"
    r"food\s+price|food\s+prices|food\s+inflation|vegetable\s+price|vegetable\s+market|"
    r"wholesale\s+market|agri|agriculture|agricultural\s+sector|agricultural\s+production|"
    r"fertilizer|pesticide|drought|flood|flooding|landslide|transport\s+strike|fuel\s+price)\b",
    re.IGNORECASE,
)

# Irrelevant Non-Market Noise Exclusion Pattern
_EXCLUDE_NOISE_PATTERN = re.compile(
    r"\b(wildlife|animal\s+welfare|elephant\s+park|zoo|cricket|entertainment|movie|film|hotel|tourism\s+award)\b",
    re.IGNORECASE,
)

def test_filtering():
    print("==================================================================================")
    print(" TESTING STRICT RELEVANCE FILTER ON LIVE NEWSAPI RESULTS")
    print("==================================================================================\n")

    queries = [
        "Sri Lanka vegetable price",
        "Sri Lanka food inflation",
        "Sri Lanka crop harvest",
        "Sri Lanka farmer market",
        "Sri Lanka agriculture",
        "tomato price Asia",
    ]

    articles, winning = fetch_raw_articles_for_queries(queries)
    print(f"Winning Query: '{winning}'")
    print(f"Total Raw Articles Returned: {len(articles)}\n")

    filtered_articles = []
    for art in articles:
        title = (art.get("title") or "").strip()
        desc = (art.get("description") or "").strip()
        blob = f"{title} {desc}".lower()

        if not title:
            continue
        if _EXCLUDE_NOISE_PATTERN.search(blob):
            print(f"  [EXCLUDED Noise] {title}")
            continue
        if not _STRICT_AGRI_MARKET_PATTERN.search(blob):
            print(f"  [EXCLUDED Non-Agri] {title}")
            continue

        print(f"  [PASSED] {title}")
        filtered_articles.append(art)


    print(f"\nFiltered Relevant Articles Count: {len(filtered_articles)}")
    if len(filtered_articles) < 2:
        print("  -> Fewer than 2 relevant articles found! System will display honest 'No relevant market news found at this time' message.")
    else:
        print("  -> 2 or more relevant articles found! Headlines to display:")
        for a in filtered_articles[:5]:
            print(f"     * {a.get('title')}")

if __name__ == "__main__":
    test_filtering()
