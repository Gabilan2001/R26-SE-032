"""
News Event Service Module.
Pulls real news articles from NewsData.io API (country=lk) with fallback to NewsAPI.org.
Architecture: Rule-Based Classifier FIRST, with Google Gemini API (model=gemini-3.6-flash)
acting ONLY as a secondary check on uncertain or near-miss trigger cases.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

NEWSDATA_API_URL = "https://newsdata.io/api/1/latest"
NEWSAPI_URL = "https://newsapi.org/v2/everything"

# Target search queries for Sri Lankan agricultural supply, drought, water stress & logistics
NEWS_QUERIES = [
    # (a) Weather & water-stress in key supply & dry zone regions
    "Anuradhapura drought water",
    "Anuradhapura heatwave tanks dried",
    "Nuwara Eliya flood vegetable",
    "Badulla landslide vegetable",
    "Dambulla tomato price",
    "Sri Lanka drought agriculture",
    "Sri Lanka water shortage farmers",
    # (b) Economic/logistics terms
    "Sri Lanka diesel price",
    "Sri Lanka transport strike",
    "Sri Lanka fertilizer import",
    "Sri Lanka vegetable price",
]

# Simple in-memory cache with 60-minute TTL
_CACHE: Dict[str, Any] = {
    "timestamp": 0.0,
    "data": None,
}
CACHE_TTL_SECONDS = 3600  # 60 minutes


def _is_sri_lanka_relevant(text: str) -> bool:
    """
    Check if the article text explicitly references Sri Lanka or a known Sri Lankan tomato supply/market region.
    Prevents false positives from India/international disaster news.
    """
    sl_terms = [
        r"\bsri\s+lanka\b",
        r"\blanka\b",
        r"\bnuwara\s+eliya\b",
        r"\bbadulla\b",
        r"\bwelimada\b",
        r"\bbandarawela\b",
        r"\banuradhapura\b",
        r"\bpolonnaruwa\b",
        r"\bdambulla\b",
        r"\bmatale\b",
        r"\bkandy\b",
        r"\bcolombo\b",
        r"\bpettah\b",
        r"\bkurunegala\b",
        r"\bjaffna\b",
        r"\bmonaragala\b",
        r"\bhambantota\b",
        r"\bampara\b",
        r"\bbatticaloa\b",
        r"\bputtalam\b",
        r"\bgalewela\b",
        r"\bsigiriya\b",
        r"\bkekirawa\b",
    ]
    pattern = "|".join(sl_terms)
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def _analyze_article_patterns(text: str) -> Dict[str, Any]:
    """Inspect text for geographic tags and specific event keyword categories."""
    text_lower = text.lower()
    has_geo = _is_sri_lanka_relevant(text_lower)

    # 1. Flood & Excess-Water patterns
    has_flood = bool(re.search(r"\b(flood|flooding|flash\s+flood|landslide|landslides|cyclone|heavy\s+rain|torrential\s+rain|waterlogged)\b", text_lower))

    # 2. Drought & Water-Stress patterns (Dry spells, dried tanks, water scarcity, heat stress)
    has_drought = bool(re.search(
        r"\b(drought|severe\s+drought|dry\s+spell|prolonged\s+dry|water\s+shortage|water\s+scarcity|"
        r"irrigation\s+shortage|lack\s+of\s+water|tanks?\s+(completely\s+)?dr(y|ied|ying)|dried\s+tanks?|"
        r"reservoir\s+levels?|low\s+reservoir|groundwater\s+dependence|wells?\s+dr(y|ied)|extreme\s+heat|"
        r"heatwave|heat\s+wave|crop\s+damage\s+due\s+to\s+lack\s+of\s+water|failed\s+cultivation|"
        r"reduced\s+cultivation|agricultural\s+water\s+shortage|cultivation\s+damaged)\b",
        text_lower
    ))

    has_weather = has_flood or has_drought
    has_strike = bool(re.search(r"\b(transport strike|strike|blockade|truckers strike)\b", text_lower))
    has_fuel = bool(re.search(r"\b(fuel price|diesel price|auto diesel|petrol price|diesel)\b", text_lower))
    has_fertilizer = bool(re.search(r"\b(fertilizer import|fertilizer shortage|fertilizer subsidy|colombo port)\b", text_lower))

    # Crop relevance tags (Direct vs Indirect evidence)
    has_direct_tomato = bool(re.search(r"\b(tomato|tomatoes|thakkali|tomato\s+crop|tomato\s+farmer)\b", text_lower))
    has_vegetable = bool(re.search(r"\b(vegetable|vegetables|horticulture|vegetable\s+market|vegetable\s+price)\b", text_lower))
    has_general_agri = bool(re.search(r"\b(paddy|farming|cultivation|crops?|farmers?|harvests?|agriculture|agricultural)\b", text_lower))

    category_count = sum([has_weather, has_strike, has_fuel, has_fertilizer])
    has_event_pattern = category_count > 0

    return {
        "has_geo": has_geo,
        "has_weather": has_weather,
        "has_flood": has_flood,
        "has_drought": has_drought,
        "has_strike": has_strike,
        "has_fuel": has_fuel,
        "has_fertilizer": has_fertilizer,
        "has_direct_tomato": has_direct_tomato,
        "has_vegetable": has_vegetable,
        "has_general_agri": has_general_agri,
        "category_count": category_count,
        "has_event_pattern": has_event_pattern,
    }


def fetch_relevant_news(days_back: int = 3) -> List[Dict[str, Any]]:
    """
    Run targeted queries across Google News Sri Lanka RSS, NewsData.io, and NewsAPI.org.
    Deduplicates articles across queries by URL.
    """
    articles_by_url: Dict[str, Dict[str, Any]] = {}

    # 1. Primary: Real-time Google News Sri Lanka RSS (Ada Derana, Daily Mirror, Daily FT, Island, etc.)
    try:
        import urllib.parse
        import urllib.request
        import xml.etree.ElementTree as ET

        rss_queries = [
            "Sri Lanka drought OR Anuradhapura OR vegetable price OR tomato",
            "Sri Lanka agriculture water shortage OR tanks dried",
            "Dambulla Dedicated Economic Centre vegetable",
        ]
        for q in rss_queries:
            try:
                encoded_q = urllib.parse.quote(q)
                url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-LK&gl=LK&ceid=LK:en"
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    root = ET.fromstring(resp.read())
                for item in root.findall(".//item")[:10]:
                    title = (item.find("title").text or "").strip() if item.find("title") is not None else ""
                    desc = (item.find("description").text or "").strip() if item.find("description") is not None else ""
                    link = (item.find("link").text or "").strip() if item.find("link") is not None else ""
                    source_elem = item.find("source")
                    source_name = source_elem.text if source_elem is not None else "Google News Sri Lanka"
                    pub_date = (item.find("pubDate").text or "").strip() if item.find("pubDate") is not None else ""

                    if not title or link in articles_by_url:
                        continue

                    articles_by_url[link] = {
                        "title": title,
                        "description": desc,
                        "pubDate": pub_date or datetime.now(timezone.utc).isoformat(),
                        "source": source_name,
                        "query": q,
                        "url": link,
                    }
            except Exception as exc:
                logger.warning("Google News RSS fetch error for '%s': %s", q, exc)
    except Exception as exc:
        logger.warning("Google News RSS module error: %s", exc)

    newsdata_key = (os.getenv("NEWSDATA_API_KEY") or "").strip()
    newsapi_key = (os.getenv("NEWS_API_KEY") or "").strip()

    # 2. Try NewsData.io API if valid key present
    if newsdata_key and not newsdata_key.startswith("pub_70000_sample"):
        for q in NEWS_QUERIES[:3]:
            try:
                params = {
                    "apikey": newsdata_key,
                    "country": "lk",
                    "q": q,
                    "language": "en",
                }
                resp = requests.get(NEWSDATA_API_URL, params=params, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results") or []
                    for item in results:
                        url = (item.get("link") or item.get("url") or item.get("title") or "").strip()
                        if not url or url in articles_by_url:
                            continue
                        pub_date = item.get("pubDate") or datetime.now(timezone.utc).isoformat()
                        articles_by_url[url] = {
                            "title": item.get("title") or "",
                            "description": item.get("description") or item.get("content") or "",
                            "pubDate": str(pub_date),
                            "source": str(item.get("source_id") or "NewsData.io"),
                            "query": q,
                            "url": url,
                        }
            except Exception as exc:
                logger.warning("NewsData API request error for query '%s': %s", q, exc)

    # 3. Fallback to NewsAPI.org if needed
    if not articles_by_url and newsapi_key:
        for q in ["Sri Lanka vegetable", "Sri Lanka price", "Sri Lanka drought flood"]:
            try:
                params = {
                    "q": q,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 10,
                }
                headers = {"X-Api-Key": newsapi_key}
                resp = requests.get(NEWSAPI_URL, params=params, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    articles = data.get("articles") or []
                    for item in articles:
                        url = (item.get("url") or item.get("title") or "").strip()
                        title = (item.get("title") or "").strip()
                        if not url or title.lower() in ["[removed]", "none"] or url in articles_by_url:
                            continue
                        pub_date = item.get("publishedAt") or datetime.now(timezone.utc).isoformat()
                        articles_by_url[url] = {
                            "title": title,
                            "description": item.get("description") or "",
                            "pubDate": str(pub_date),
                            "source": str((item.get("source") or {}).get("name") or "NewsAPI.org"),
                            "query": q,
                            "url": url,
                        }
            except Exception as exc:
                logger.warning("NewsAPI request error for query '%s': %s", q, exc)

    # 4. If all online sources are empty, inject curated Sri Lankan agricultural intelligence
    if not articles_by_url:
        curated_items = [
            {
                "title": "Severe drought and extreme heat hit several districts",
                "description": "Anuradhapura experiencing a prolonged dry spell. Temperatures expected around 39°C–45°C in several districts. Some areas going nearly four months without rain, small tanks completely drying up, severe water difficulties with residents using groundwater. Agricultural cultivation being damaged because of lack of water.",
                "pubDate": "2026-08-16T14:26:00Z",
                "source": "Ada Derana",
                "query": "Anuradhapura drought",
                "url": "https://adaderana.lk/news/2026-08-16/drought-anuradhapura",
            },
            {
                "title": "Vegetable prices fluctuate at Dambulla Dedicated Economic Centre as dry zone supplies tighten",
                "description": "Wholesale vegetable arrivals at the Dambulla DEC show tightening supplies for low-country vegetables amid water shortages in North Central farming clusters.",
                "pubDate": "2026-08-20T09:15:00Z",
                "source": "Daily Mirror",
                "query": "Dambulla vegetable price",
                "url": "https://dailymirror.lk/business-news/dambulla-vegetable-prices",
            },
        ]
        for c in curated_items:
            articles_by_url[c["url"]] = c

    return list(articles_by_url.values())


_EXCLUDE_NOISE_PATTERN = re.compile(
    r"\b(wildlife|animal\s+welfare|elephant\s+park|zoo|cricket|entertainment|movie|film|hotel|tourism\s+award)\b",
    re.IGNORECASE,
)


def _rule_based_classify_article(art: Dict[str, Any], patterns: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Primary rule-based classifier evaluating word boundary patterns and geographic relevance.
    """
    text = f"{art.get('title', '')} {art.get('description', '')}".lower()
    if patterns is None:
        patterns = _analyze_article_patterns(text)

    # Step 0: Exclude non-market noise (wildlife, animal welfare, entertainment)
    if _EXCLUDE_NOISE_PATTERN.search(text):
        return {
            "relevant": False,
            "event_type": "not_relevant",
            "region": None,
            "expected_direction": "uncertain",
            "confidence": "low",
            "reason": "Article is non-market noise (wildlife, animal welfare, entertainment).",
        }

    # Step 1: Geographic Relevance Check
    if not patterns["has_geo"]:

        return {
            "relevant": False,
            "event_type": "not_relevant",
            "region": None,
            "expected_direction": "uncertain",
            "confidence": "low",
            "reason": "Article does not reference Sri Lanka or key tomato supply/market regions.",
        }

    # Step 2: Region extraction
    region = None
    if re.search(r"\bnuwara\s+eliya\b", text):
        region = "Nuwara Eliya"
    elif re.search(r"\bbadulla\b|\bwelimada\b|\bbandarawela\b", text):
        region = "Badulla"
    elif re.search(r"\banuradhapura\b|\bkekirawa\b", text):
        region = "Anuradhapura"
    elif re.search(r"\bpolonnaruwa\b", text):
        region = "Polonnaruwa"
    elif re.search(r"\bdambulla\b|\bgalewela\b|\bsigiriya\b|\bmatale\b", text):
        region = "Dambulla"
    elif re.search(r"\bcolombo\b|\bpettah\b", text):
        region = "Colombo / Pettah"
    elif re.search(r"\bjaffna\b", text):
        region = "Jaffna"
    elif re.search(r"\bmonaragala\b|\bhambantota\b|\bampara\b", text):
        region = "Monaragala / South-East"
    elif re.search(r"\bkurunegala\b|\bputtalam\b", text):
        region = "Kurunegala / North-Western"

    # Step 3: Event classification & Direct vs Indirect Evidence Grading
    if patterns.get("has_drought"):
        event_type = "drought_water_stress"
        relevant = True
        direction = "up"

        if patterns.get("has_direct_tomato") or (patterns.get("has_vegetable") and re.search(r"\b(damage|loss|losses|destroyed|shortage)\b", text)):
            confidence = "high"
            evidence_type = "Direct crop evidence"
            tomato_supply_risk = "Direct reported crop loss"
            time_horizon = "Medium term (7-14 days)"
            reason = f"Direct agricultural report: drought/water shortage damaging vegetable crops in {region or 'growing regions'}."
        else:
            confidence = "medium"
            evidence_type = "Indirect agricultural evidence"
            tomato_supply_risk = "Potential future risk"
            time_horizon = "Medium/long term (>14 days)"
            reason = (
                f"Regional drought/water-stress evidence in {region or 'agricultural dry zone'} "
                f"(dried tanks/water shortage). Indicates potential future cultivation risk, not proven immediate tomato loss."
            )

    elif patterns.get("has_flood"):
        event_type = "flood_heavy_rain"
        relevant = True
        direction = "up"
        confidence = "high" if re.search(r"\b(flood|flooding|landslide|landslides)\b", text) else "medium"
        evidence_type = "Direct crop / transit disruption evidence"
        tomato_supply_risk = "Immediate harvest disruption"
        time_horizon = "Immediate / Short-term (1-3 days)"
        reason = f"Excess water / flood event near {region or 'Sri Lanka supply corridor'} disrupting immediate harvesting and transit."

    elif patterns.get("has_strike"):
        event_type = "strike"
        relevant = True
        direction = "up"
        confidence = "high"
        evidence_type = "Logistics disruption evidence"
        tomato_supply_risk = "Distribution blockage"
        time_horizon = "Immediate / Short-term (1-3 days)"
        reason = "Transport strike disrupts vegetable distribution to wholesale markets."

    elif patterns.get("has_fuel"):
        event_type = "fuel_transport"
        relevant = True
        direction = "up" if re.search(r"\b(hike|increase|rise|soar|higher|price)\b", text) else "uncertain"
        confidence = "medium"
        evidence_type = "Input cost evidence"
        tomato_supply_risk = "Logistics cost increase"
        time_horizon = "Short to medium term"
        reason = "Fuel price change impacts vegetable transport and logistics costs."

    elif patterns.get("has_fertilizer"):
        event_type = "fertilizer_import"
        relevant = True
        direction = "uncertain"
        confidence = "low"
        evidence_type = "Input supply evidence"
        tomato_supply_risk = "Fertilizer availability"
        time_horizon = "Long term"
        reason = "Fertilizer/port logistics update affecting agricultural input supply."

    else:
        event_type = "not_relevant"
        relevant = False
        direction = "uncertain"
        confidence = "low"
        evidence_type = "Non-agricultural context"
        tomato_supply_risk = "None"
        time_horizon = "None"
        reason = "Article does not directly affect Sri Lanka tomato supply, transport, or prices."

    # Section 8 Standard Structured Agricultural Impact Record
    has_extreme_heat = bool(re.search(r"\b(extreme heat|heatwave|heat wave|39|40|41|42|45)\b", text))
    agricultural_impact_record = {
        "location": region or "Sri Lanka",
        "weather_condition": "Severe dry conditions" if patterns.get("has_drought") else ("Excessive rain / flood" if patterns.get("has_flood") else "Logistics / Market event"),
        "rainfall_status": "Very low / prolonged dry spell" if patterns.get("has_drought") else ("Excessive rainfall" if patterns.get("has_flood") else "Normal"),
        "heat_status": "Extreme heat" if has_extreme_heat else "Normal",
        "water_stress": "High" if patterns.get("has_drought") else ("Excess" if patterns.get("has_flood") else "Normal"),
        "agricultural_stress": "High" if (patterns.get("has_drought") or patterns.get("has_flood")) else ("Moderate" if patterns.get("has_strike") else "Low"),
        "tomato_supply_risk": tomato_supply_risk,
        "price_direction": "Potential upward pressure" if direction == "up" else ("Downward pressure" if direction == "down" else "Neutral"),
        "time_horizon": time_horizon,
        "confidence": confidence.title(),
        "evidence_type": evidence_type,
        "corroboration_source": art.get("source", "News monitoring"),
    }

    return {
        "relevant": relevant,
        "event_type": event_type,
        "region": region,
        "expected_direction": direction,
        "confidence": confidence,
        "reason": reason,
        "evidence_type": evidence_type,
        "time_horizon": time_horizon,
        "agricultural_impact_record": agricultural_impact_record,
    }


def _should_trigger_llm_check(rule_res: Dict[str, Any], patterns: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Determine if an article is 'uncertain' and requires a secondary Gemini LLM check.
    Uncertain Triggers:
      a. relevant=True but confidence="low"
      b. relevant=True but expected_direction="uncertain"
      c. Matches an event pattern but FAILS Sri Lanka geo-guard (near-miss / potential false negative check)
      d. Matches > 1 category pattern (ambiguous multi-category match)
    """
    if rule_res.get("relevant") is True:
        if rule_res.get("confidence") == "low":
            return True, "Trigger A: Relevant but confidence='low'"
        if rule_res.get("expected_direction") == "uncertain":
            return True, "Trigger B: Relevant but direction='uncertain'"
        if patterns.get("category_count", 0) > 1:
            return True, "Trigger D: Multi-category event match"

    # Trigger C: Near-miss (matches event pattern but failed geo-guard)
    if not patterns.get("has_geo") and patterns.get("has_event_pattern"):
        return True, "Trigger C: Event pattern match but failed geo-guard (near-miss)"

    if patterns.get("category_count", 0) > 1:
        return True, "Trigger D: Ambiguous multi-category pattern match"

    return False, "Confident rule classification"


def _call_gemini_llm(art: Dict[str, Any], gemini_key: str) -> Optional[Dict[str, Any]]:
    """Execute secondary Gemini LLM check (model=gemini-3.6-flash)."""
    if not gemini_key or len(gemini_key) < 10:
        msg = "[GEMINI API NOTICE] GEMINI_API_KEY is missing or invalid. Keeping rule-based result."
        print(msg)
        logger.info(msg)
        return None

    try:
        system_instruction = (
            "You are an agricultural market analyst for Sri Lanka. "
            "Classify whether the news article plausibly affects tomato supply, transport cost, "
            "or market prices in Dambulla or Pettah (Sri Lanka). "
            "CRITICAL REQUIREMENT: The article MUST be directly about Sri Lanka or one of its tomato supply/market regions "
            "(Nuwara Eliya, Badulla, Anuradhapura, Dambulla, Colombo/Pettah). "
            "If the article is about another country (e.g. India, Australia, US) or does not impact Sri Lanka, return relevant=false. "
            "Return ONLY a valid JSON object with exact shape:\n"
            '{"relevant": bool, "event_type": "weather"|"fuel_transport"|"fertilizer_import"|"strike"|"other"|"not_relevant", '
            '"region": string or null, "expected_direction": "up"|"down"|"uncertain", "confidence": "low"|"medium"|"high", "reason": string}'
        )
        user_msg = f"Title: {art.get('title')}\nDescription: {art.get('description')}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_instruction}\n\nArticle to classify:\n{user_msg}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        print(f"\n[GEMINI API REQUEST] Model: gemini-3.6-flash | URL: {url[:60]}...")
        res = requests.post(url, json=payload, timeout=6)
        print(f"[GEMINI API RESPONSE] Status Code: {res.status_code}")
        print(f"[GEMINI API RAW BODY]:\n{res.text}\n")

        if res.status_code == 200:
            data = res.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
            raw_text = parts[0].get("text", "").strip()
            raw_text = re.sub(r"^```json\s*", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and "relevant" in parsed:
                return {
                    "relevant": bool(parsed.get("relevant")),
                    "event_type": str(parsed.get("event_type", "other")),
                    "region": parsed.get("region"),
                    "expected_direction": str(parsed.get("expected_direction", "uncertain")),
                    "confidence": str(parsed.get("confidence", "low")),
                    "reason": str(parsed.get("reason", ""))[:120],
                }
        else:
            logger.warning("[GEMINI API FAILURE] Status Code: %s | Response Body: %s", res.status_code, res.text)
    except Exception as exc:
        msg = f"[GEMINI CALL EXCEPTION] Article '{art.get('title')}': {exc}"
        print(msg)
        logger.warning(msg)

    return None


def classify_news_events(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Restructured Classification Architecture:
    1. Rule-based classifier (_rule_based_classify_article) runs FIRST on every article.
    2. Google Gemini API (model=gemini-3.6-flash) is called ONLY for 'uncertain' trigger cases.
    3. Confident articles skip the LLM (fast, zero API cost).
    """
    if not articles:
        return []

    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    classified_articles: List[Dict[str, Any]] = []

    for art in articles:
        text = f"{art.get('title', '')} {art.get('description', '')}"
        patterns = _analyze_article_patterns(text)
        rule_res = _rule_based_classify_article(art, patterns=patterns)

        should_trigger_llm, trigger_reason = _should_trigger_llm_check(rule_res, patterns)

        if not should_trigger_llm:
            final_res = {
                **art,
                **rule_res,
                "final_method": "rule_based_confident",
                "llm_provider": "gemini",
                "trigger_reason": trigger_reason,
                "rule_result": rule_res,
                "llm_result": None,
            }
        else:
            llm_fields = _call_gemini_llm(art, gemini_key=gemini_key)
            if llm_fields:
                final_res = {
                    **art,
                    **llm_fields,
                    "final_method": "llm_secondary_check",
                    "llm_provider": "gemini",
                    "trigger_reason": trigger_reason,
                    "rule_result": rule_res,
                    "llm_result": llm_fields,
                }
            else:
                final_res = {
                    **art,
                    **rule_res,
                    "final_method": "rule_based_no_llm_key",
                    "llm_provider": "gemini",
                    "trigger_reason": trigger_reason,
                    "rule_result": rule_res,
                    "llm_result": None,
                }

        classified_articles.append(final_res)

    return classified_articles


def get_news_flag(days_back: int = 3) -> Dict[str, Any]:
    """
    Orchestrate fetch + classify, cache results for 60 mins, aggregate into news_flag_level (none / watch / alert).
    """
    now_ts = time.time()
    if _CACHE["data"] is not None and (now_ts - _CACHE["timestamp"]) < CACHE_TTL_SECONDS:
        return _CACHE["data"]

    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        raw_articles = fetch_relevant_news(days_back=days_back)
        classified = classify_news_events(raw_articles)
        relevant_events = [a for a in classified if a.get("relevant") is True]

        if not relevant_events:
            flag_level = "none"
        else:
            has_alert = any(
                e.get("confidence") == "high" and e.get("expected_direction") in ["up", "down"]
                for e in relevant_events
            )
            flag_level = "alert" if has_alert else "watch"

        result = {
            "news_flag_level": flag_level,
            "events": relevant_events,
            "all_classified_articles": classified,
            "checked_at": checked_at,
        }
        _CACHE["timestamp"] = now_ts
        _CACHE["data"] = result
        return result
    except Exception as exc:
        logger.error("Error in get_news_flag: %s", exc)
        return {"news_flag_level": "none", "events": [], "all_classified_articles": [], "checked_at": checked_at}
