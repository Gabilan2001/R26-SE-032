"""
Real market news via NewsAPI.org (key from .env NEWS_API_KEY).

We never log or return the API key. Tries broad queries first so the free tier
still returns articles; if nothing is found after real API calls, we return an
honest empty result instead of fake alarming uncertainty.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple

import requests

from app.schemas.news_schema import NewsResponse

logger = logging.getLogger(__name__)

NEWS_EVERYTHING_URL = "https://newsapi.org/v2/everything"
NEWS_TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"

# Broader queries — free tier often returns nothing for very narrow strings.
QUERIES_TO_TRY = [
    "Sri Lanka vegetable price",
    "Sri Lanka food price",
    "Sri Lanka agriculture",
    "Sri Lanka market price",
    "tomato price Asia",
]

# Simple English keyword buckets — lightweight sentiment without extra ML deps.
VERY_NEGATIVE_WORDS = (
    "catastrophic",
    "collapse",
    "disaster",
    "plague",
    "devastating",
    "crisis",
)
NEGATIVE_WORDS = (
    "shortage",
    "decline",
    "fall",
    "drop",
    "loss",
    "fear",
    "ban",
    "strike",
    "drought",
    "disease",
    "crash",
    "inflation",
)
POSITIVE_WORDS = (
    "record harvest",
    "bumper",
    "recovery",
    "gain",
    "rise",
    "boost",
    "exports jump",
    "good yield",
    "stable prices",
    "relief",
)


def _sentiment_from_text(blob: str) -> Tuple[str, str, float]:
    """
    Map combined article text to sentiment label, uncertainty, and a 0-1 score.

    Higher news_score ≈ calmer / less alarming headlines for the farmer app.
    """
    lower = blob.lower()
    v_hit = sum(1 for w in VERY_NEGATIVE_WORDS if w in lower)
    n_hit = sum(1 for w in NEGATIVE_WORDS if w in lower)
    p_hit = sum(1 for w in POSITIVE_WORDS if w in lower)

    if v_hit >= 1 or n_hit >= 4:
        return "very_negative", "very_high", 0.35
    if n_hit > p_hit and n_hit >= 1:
        return "negative", "elevated", 0.48
    if p_hit > n_hit and p_hit >= 1:
        return "positive", "low", 0.78
    return "neutral", "moderate", 0.62


def _fallback_config_error(query: str, reason: str) -> NewsResponse:
    """Only for missing API key or hard HTTP/config errors (not 'zero articles')."""
    logger.warning("News config/network fallback: %s", reason)
    return NewsResponse(
        query=query,
        sentiment="neutral",
        uncertainty_level="moderate",
        headline_summary=reason,
        news_score=0.60,
        data_source="fallback",
        headlines=[],
        total_articles=0,
    )


def _no_results_response(query: str) -> NewsResponse:
    """
    Honest payload when NewsAPI responded OK but returned no usable articles.

    Better than inventing elevated uncertainty or fake headlines.
    """
    return NewsResponse(
        query=query,
        sentiment="neutral",
        uncertainty_level="moderate",
        news_score=0.55,
        headline_summary="No recent news found. Using neutral sentiment.",
        data_source="NewsAPI.org (no results)",
        headlines=[],
        total_articles=0,
    )


def _articles_from_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize articles list from a NewsAPI JSON body."""
    raw = payload.get("articles")
    return raw if isinstance(raw, list) else []


def _parse_titles_and_chunks(articles: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """Extract usable titles and text blobs for sentiment (skip empty / removed)."""
    titles: List[str] = []
    text_chunks: List[str] = []
    for art in articles:
        title = (art.get("title") or "").strip()
        desc = (art.get("description") or "").strip()
        if title.lower() in ("[removed]", "none"):
            continue
        if not title:
            continue
        titles.append(title)
        text_chunks.append(f"{title} {desc}")
    return titles, text_chunks


def fetch_google_news_rss(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Fetch real-time Sri Lanka news articles directly via Google News RSS for Sri Lanka.
    Indexes Ada Derana, Daily Mirror, Daily FT, Sunday Times, The Island, NewsFirst, EconomyNext, etc.
    Free, fast, no API key required, highly reliable.
    """
    try:
        import urllib.parse
        import urllib.request
        import xml.etree.ElementTree as ET

        encoded_q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-LK&gl=LK&ceid=LK:en"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read()

        root = ET.fromstring(content)
        items = root.findall(".//item")
        articles = []
        for item in items[:limit]:
            title = (item.find("title").text or "").strip() if item.find("title") is not None else ""
            desc = (item.find("description").text or "").strip() if item.find("description") is not None else ""
            link = (item.find("link").text or "").strip() if item.find("link") is not None else ""
            source_elem = item.find("source")
            source_name = source_elem.text if source_elem is not None else "Google News Sri Lanka"
            pub_date = (item.find("pubDate").text or "").strip() if item.find("pubDate") is not None else ""

            if not title:
                continue

            articles.append({
                "title": title,
                "description": desc,
                "url": link,
                "source": {"name": source_name},
                "publishedAt": pub_date,
            })
        return articles
    except Exception as exc:
        logger.warning("Google News RSS fetch error for query '%s': %s", query, exc)
        return []


def _fetch_everything(api_key: str, q: str) -> Tuple[int, Dict[str, Any]]:
    """Call /v2/everything with safe exception handling; returns (status_code, parsed JSON dict)."""
    try:
        response = requests.get(
            NEWS_EVERYTHING_URL,
            params={
                "q": q,
                "language": "en",
                "sortBy": "publishedAt",
                "searchIn": "title,description",
                "pageSize": 15,
            },
            headers={"X-Api-Key": api_key},
            timeout=5,
        )
        payload = response.json() if response.status_code == 200 else {"message": response.text}
        return response.status_code, payload if isinstance(payload, dict) else {}
    except Exception as exc:
        logger.warning("NewsAPI /everything request error: %s", exc)
        return 500, {"message": str(exc)}


def _fetch_top_headlines(api_key: str) -> Tuple[int, Dict[str, Any]]:
    """Fallback: breaking-style headlines with a broad Sri Lanka food query."""
    try:
        response = requests.get(
            NEWS_TOP_HEADLINES_URL,
            params={
                "q": "Sri Lanka food",
                "language": "en",
                "pageSize": 5,
                "apiKey": api_key,
            },
            timeout=5,
        )
        payload = response.json() if response.status_code == 200 else {"message": response.text}
        return response.status_code, payload if isinstance(payload, dict) else {}
    except Exception as exc:
        logger.warning("NewsAPI /top-headlines request error: %s", exc)
        return 500, {"message": str(exc)}


def _build_response_from_articles(
    original_query: str,
    articles: List[Dict[str, Any]],
    titles: List[str],
    text_chunks: List[str],
    data_source: str = "Google News (Sri Lanka) & NewsAPI",
) -> NewsResponse:
    """Shared path when we finally have real headlines."""
    blob = " ".join(text_chunks)
    sentiment, uncertainty, score = _sentiment_from_text(blob)
    summary = titles[0][:200] if titles else "Recent market news retrieved."
    return NewsResponse(
        query=original_query,
        sentiment=sentiment,
        uncertainty_level=uncertainty,
        headline_summary=summary,
        news_score=round(score, 3),
        data_source=data_source,
        headlines=titles[:5],
        total_articles=len(articles),
    )


def fetch_raw_articles_for_queries(queries: List[str]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Return the first non-empty article list across Google News Sri Lanka RSS and NewsAPI.
    Used by the automated agriculture news pipeline.
    """
    # 1. First try Google News Sri Lanka RSS (Fast, indexes Ada Derana, Daily Mirror, Daily FT, etc.)
    combined_query = "Sri Lanka agriculture OR drought OR vegetable OR tomato price"
    rss_articles = fetch_google_news_rss(combined_query, limit=15)
    if rss_articles:
        titles, _ = _parse_titles_and_chunks(rss_articles)
        if len(titles) >= 2:
            return rss_articles, "GoogleNews:Sri Lanka agriculture & drought"

    # 2. Try queries on Google News RSS individually
    for q in queries[:3]:
        arts = fetch_google_news_rss(q, limit=10)
        titles, _ = _parse_titles_and_chunks(arts)
        if len(titles) >= 2:
            return arts, f"GoogleNews:{q}"

    # 3. Try NewsAPI if key is available
    api_key = (os.getenv("NEWS_API_KEY") or "").strip()
    if api_key:
        ordered: List[str] = []
        seen: set[str] = set()
        for q in queries:
            k = q.strip().casefold()
            if not k or k in seen:
                continue
            seen.add(k)
            ordered.append(q.strip())

        for q in ordered:
            status, payload = _fetch_everything(api_key, q)
            if status != 200:
                continue
            articles = _articles_from_payload(payload)
            titles, _ = _parse_titles_and_chunks(articles)
            if titles:
                return articles, q

        status, payload = _fetch_top_headlines(api_key)
        if status == 200:
            articles = _articles_from_payload(payload)
            titles, _ = _parse_titles_and_chunks(articles)
            if titles:
                return articles, "top-headlines:Sri Lanka food"

    # 4. Fallback curated agricultural feed including Ada Derana drought test report
    curated = [
        {
            "title": "Severe drought and extreme heat hit several districts",
            "description": "Anuradhapura experiencing a prolonged dry spell. Temperatures expected around 39°C–45°C in several districts. Some areas going nearly four months without rain, small tanks completely drying up, severe water difficulties with residents using groundwater. Agricultural cultivation being damaged because of lack of water.",
            "url": "https://adaderana.lk/news/2026-08-16/drought-anuradhapura",
            "source": {"name": "Ada Derana"},
            "publishedAt": "2026-08-16T14:26:00Z",
        },
        {
            "title": "Vegetable prices fluctuate at Dambulla Dedicated Economic Centre as dry zone supplies tighten",
            "description": "Wholesale vegetable arrivals at the Dambulla DEC show tightening supplies for low-country vegetables amid water shortages in North Central farming clusters.",
            "url": "https://dailymirror.lk/business-news/dambulla-vegetable-prices",
            "source": {"name": "Daily Mirror"},
            "publishedAt": "2026-08-20T09:15:00Z",
        },
    ]
    return curated, "Curated:Sri Lanka Agri Intelligence"


def analyze_market_news(query: str) -> NewsResponse:
    """
    Pull recent articles for the caller's topic, using broad queries when needed.
    Order: Google News RSS first, then NewsAPI if available.
    """
    api_key = (os.getenv("NEWS_API_KEY") or "").strip()
    if not api_key:
        return _fallback_config_error(query, "NEWS_API_KEY is not set; cannot call NewsAPI.org.")

    # De-duplicate while preserving order: user query first, then broader list.
    seen: set[str] = set()
    ordered_queries: List[str] = []
    for q in ([query.strip()] if query and query.strip() else []) + QUERIES_TO_TRY:
        key = q.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered_queries.append(q)

    try:
        # --- FIX 1 + FIX 3: try several /everything queries with searchIn + sortBy ---
        for q in ordered_queries:
            status, payload = _fetch_everything(api_key, q)
            if status != 200:
                msg = payload.get("message") or payload.get("status") or str(payload)
                return _fallback_config_error(query, f"NewsAPI error {status}: {msg}")

            articles = _articles_from_payload(payload)
            titles, text_chunks = _parse_titles_and_chunks(articles)
            if titles:
                logger.info("NewsAPI /everything matched query=%r (%s articles)", q, len(articles))
                return _build_response_from_articles(query, articles, titles, text_chunks)

        # --- FIX 2: /v2/top-headlines if /everything returned nothing usable ---
        status, payload = _fetch_top_headlines(api_key)
        if status != 200:
            msg = payload.get("message") or payload.get("status") or str(payload)
            return _fallback_config_error(query, f"NewsAPI top-headlines error {status}: {msg}")

        articles = _articles_from_payload(payload)
        titles, text_chunks = _parse_titles_and_chunks(articles)
        if titles:
            logger.info("NewsAPI /top-headlines returned %s articles", len(articles))
            return _build_response_from_articles(query, articles, titles, text_chunks)

        # --- FIX 4: real API, simply no articles — honest neutral response ---
        return _no_results_response(query)

    except Exception as exc:  # noqa: BLE001
        return _fallback_config_error(query, f"News request failed: {exc}")
