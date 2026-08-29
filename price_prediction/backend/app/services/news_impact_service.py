"""
Automatic filtering and impact scoring for agriculture / tomato-related news.

The farmer never types a news query — the backend builds queries from location
and applies keyword + topic rules suitable for a beginner-friendly pipeline.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Tuple

from app.schemas.market_news_schema import NewsMarketAnalysis
from app.services.news_service import _parse_titles_and_chunks, fetch_raw_articles_for_queries

# Articles must mention at least one genuine agricultural / market / crop supply term.
_RELEVANCE_PATTERN = re.compile(
    r"\b(tomato|tomatoes|vegetable|vegetables|crop|crops|harvest|harvests|farm|farmers|farming|"
    r"food\s+price|food\s+prices|food\s+inflation|vegetable\s+price|vegetable\s+market|"
    r"wholesale\s+market|agri|agriculture|agricultural\s+sector|agricultural\s+production|"
    r"fertilizer|pesticide|drought|flood|flooding|landslide|transport\s+strike|fuel\s+price)\b",
    re.IGNORECASE,
)

# Exclude non-market noise (wildlife, zoo, animal welfare, entertainment)
_EXCLUDE_NOISE_PATTERN = re.compile(
    r"\b(wildlife|animal\s+welfare|elephant\s+park|zoo|cricket|entertainment|movie|film|hotel|tourism\s+award)\b",
    re.IGNORECASE,
)

# Strong signals that often push tomato prices UP (supply risk / cost pressure).
_UP_PRICE_KEYWORDS: Tuple[str, ...] = (
    "flood",
    "heavy rain",
    "landslide",
    "transport strike",
    "strike",
    "shortage",
    "export ban",
    "import ban",
    "disease",
    "pest",
    "drought",
    "inflation",
    "fuel price",
    "diesel",
    "container",
    "delay at port",
)

# Signals that can soften prices or add supply.
_DOWN_PRICE_KEYWORDS: Tuple[str, ...] = (
    "bumper",
    "record harvest",
    "surplus",
    "imports arrive",
    "price fall",
    "prices fall",
    "subsidy",
    "relief package",
)


def _normalize_blob(title: str, desc: str) -> str:
    return f"{title} {desc}".lower()


def _detect_topics(blob: str) -> Set[str]:
    topics: Set[str] = set()
    for phrase in _UP_PRICE_KEYWORDS:
        if phrase in blob:
            topics.add(phrase.replace(" ", "_"))
    for phrase in _DOWN_PRICE_KEYWORDS:
        if phrase in blob:
            topics.add(phrase.replace(" ", "_"))
    return topics


def _score_direction(blob: str) -> Tuple[str, List[str]]:
    """Return price_impact_direction and matched topic labels."""
    up = sum(1 for p in _UP_PRICE_KEYWORDS if p in blob)
    down = sum(1 for p in _DOWN_PRICE_KEYWORDS if p in blob)
    topics = sorted(_detect_topics(blob))

    if up == 0 and down == 0:
        return "neutral", topics
    if up > down:
        return "increase", topics
    if down > up:
        return "decrease", topics
    return "uncertain", topics


def _map_to_sentiment(price_direction: str, uncertainty: str) -> str:
    """Bridge keyword economics to the simple sentiment buckets used in confidence."""
    if price_direction == "increase":
        return "negative"  # volatile / costly environment for planning
    if price_direction == "decrease":
        return "positive"
    if price_direction == "uncertain":
        return "negative" if uncertainty in ("elevated", "very_high") else "neutral"
    return "neutral"


def analyze_agriculture_news_for_location(location: str) -> NewsMarketAnalysis:
    """
    Fetch and analyse news automatically for the user's market / region label.

    Steps:
      1) Build broad Sri Lanka + agriculture queries including the location name.
      2) Pull raw articles via NewsAPI (shared low-level client).
      3) Keep only genuine tomato / agri / market-relevant rows (excluding non-market noise).
      4) If fewer than 2 relevant articles pass, return an honest empty result.
      5) Classify likely price pressure and summarise for farmers.
    """
    loc = (location or "Sri Lanka").strip()
    queries = [
        f"Sri Lanka vegetable price {loc}",
        f"Sri Lanka food inflation {loc}",
        f"Sri Lanka crop harvest {loc}",
        f"Sri Lanka farmer market {loc}",
        "Sri Lanka vegetable price",
        "Sri Lanka food inflation",
        "Sri Lanka agriculture",
        "tomato price Asia",
    ]

    articles, winning = fetch_raw_articles_for_queries(queries)
    if not articles:
        return NewsMarketAnalysis(
            price_impact_direction="neutral",
            market_impact_summary="No recent news found. Using neutral sentiment.",
            matched_topics=[],
            relevant_headlines=[],
            articles_analyzed=0,
            uncertainty_level="moderate",
            news_sentiment="neutral",
            news_score=0.55,
            data_source="NewsAPI.org (no results)",
        )

    filtered: List[Dict[str, Any]] = []
    blobs: List[str] = []
    headlines: List[str] = []
    for art in articles:
        title = (art.get("title") or "").strip()
        desc = (art.get("description") or "").strip()
        blob = _normalize_blob(title, desc)
        
        # Exclude empty titles, non-market noise, or non-agri topics
        if not title:
            continue
        if _EXCLUDE_NOISE_PATTERN.search(blob):
            continue
        if not _RELEVANCE_PATTERN.search(blob):
            continue

        filtered.append(art)
        blobs.append(blob)
        headlines.append(title)

    # User requirement: If fewer than 2 relevant articles pass, return honest empty state
    if len(filtered) < 2:
        return NewsMarketAnalysis(
            price_impact_direction="neutral",
            market_impact_summary="No major supply alerts reported in recent news monitoring.",
            matched_topics=[],
            relevant_headlines=[],
            articles_analyzed=len(filtered),
            uncertainty_level="moderate",
            news_sentiment="neutral",
            news_score=0.55,
            data_source="NewsAPI.org",
        )

    mega_blob = " ".join(blobs)

    direction, topics = _score_direction(mega_blob)
    _, chunks = _parse_titles_and_chunks(filtered)
    joined = " ".join(chunks)

    # Uncertainty scales with how alarming the language is.
    v_hit = sum(1 for w in ("catastrophic", "collapse", "disaster") if w in joined)
    n_hit = sum(1 for w in ("crisis", "shortage", "strike", "flood", "disease") if w in joined)
    if v_hit:
        uncertainty = "very_high"
    elif n_hit >= 3:
        uncertainty = "elevated"
    elif n_hit >= 1:
        uncertainty = "moderate"
    else:
        uncertainty = "low"

    sentiment = _map_to_sentiment(direction, uncertainty)
    score = 0.45 if sentiment == "very_negative" else 0.52 if sentiment == "negative" else 0.68 if sentiment == "positive" else 0.60

    summary = (
        f"Headlines around {loc} suggest {direction} pressure on tomato markets, "
        f"based on {len(filtered)} relevant articles (query: {winning})."
    )

    return NewsMarketAnalysis(
        price_impact_direction=direction,
        market_impact_summary=summary,
        matched_topics=topics,
        relevant_headlines=headlines[:8],
        articles_analyzed=len(filtered),
        uncertainty_level=uncertainty,
        news_sentiment=sentiment,
        news_score=round(score, 3),
        data_source="NewsAPI.org",
    )
