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
    r"fertilizer|pesticide|drought|severe\s+drought|dry\s+spell|prolonged\s+dry|water\s+shortage|"
    r"water\s+scarcity|irrigation\s+shortage|dried\s+tanks?|tanks?\s+dr(y|ied)|low\s+reservoir|"
    r"groundwater|extreme\s+heat|heatwave|heat\s+wave|failed\s+cultivation|agricultural\s+water\s+shortage|"
    r"flood|flooding|landslide|transport\s+strike|fuel\s+price)\b",
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
    "severe drought",
    "dry spell",
    "water shortage",
    "water scarcity",
    "irrigation shortage",
    "dried tanks",
    "tanks completely dry",
    "low reservoir",
    "extreme heat",
    "heatwave",
    "failed cultivation",
    "agricultural water shortage",
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

_LOCATIONS_REGEX = re.compile(
    r"\b(Anuradhapura|Polonnaruwa|Badulla|Nuwara Eliya|Dambulla|Matale|Kandy|Colombo|Pettah|Kurunegala|Jaffna|Monaragala|Hambantota|Ampara|Batticaloa|Puttalam|Galewela|Sigiriya|Kekirawa|Welimada)\b",
    re.IGNORECASE,
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


def _extract_agricultural_records(filtered_articles: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Generate Section 8 structured agricultural impact records for detected locations."""
    records: List[Dict[str, Any]] = []
    detected_locations: Set[str] = set()

    for art in filtered_articles:
        title = art.get("title", "")
        desc = art.get("description", "")
        text = f"{title} {desc}".lower()

        # Find locations mentioned
        loc_matches = _LOCATIONS_REGEX.findall(f"{title} {desc}")
        loc_name = loc_matches[0].title() if loc_matches else "Sri Lanka Agricultural Region"
        if loc_matches:
            detected_locations.add(loc_name)

        has_drought = bool(re.search(r"\b(drought|dry spell|water shortage|water scarcity|irrigation|dried tanks?|heatwave|extreme heat)\b", text))
        has_flood = bool(re.search(r"\b(flood|flooding|landslide|heavy rain)\b", text))
        has_direct_tomato = bool(re.search(r"\b(tomato|tomatoes|vegetable|thakkali)\b", text))
        has_extreme_heat = bool(re.search(r"\b(extreme heat|heatwave|39|40|41|42|45)\b", text))

        if has_drought:
            if has_direct_tomato and re.search(r"\b(damage|loss|shortage)\b", text):
                ev_type = "Direct crop evidence"
                supply_risk = "Direct reported crop loss"
                conf = "High"
                t_horiz = "Medium term (7-14 days)"
            else:
                ev_type = "Indirect agricultural evidence"
                supply_risk = "Potential future risk"
                conf = "Medium"
                t_horiz = "Medium/long term (>14 days)"
            cond = "Severe dry conditions"
            rain_stat = "Very low / prolonged dry spell"
            w_stress = "High"
        elif has_flood:
            ev_type = "Direct crop / transit disruption evidence"
            supply_risk = "Immediate harvest disruption"
            conf = "High"
            t_horiz = "Immediate / Short-term (1-3 days)"
            cond = "Excessive rain / flood"
            rain_stat = "Excessive rainfall"
            w_stress = "Excess"
        else:
            ev_type = "Market / logistics evidence"
            supply_risk = "Transport / Input cost pressure"
            conf = "Medium"
            t_horiz = "Short to medium term"
            cond = "Market / logistics event"
            rain_stat = "Normal"
            w_stress = "Normal"

        rec = {
            "location": loc_name,
            "weather_condition": cond,
            "rainfall_status": rain_stat,
            "heat_status": "Extreme heat" if has_extreme_heat else "Normal",
            "water_stress": w_stress,
            "agricultural_stress": "High" if (has_drought or has_flood) else "Moderate",
            "tomato_supply_risk": supply_risk,
            "price_direction": "Potential upward pressure",
            "time_horizon": t_horiz,
            "confidence": conf,
            "evidence_type": ev_type,
            "corroboration_source": str(art.get("source", "News monitoring")),
        }
        records.append(rec)

    return records, sorted(list(detected_locations))


def analyze_agriculture_news_for_location(location: str) -> NewsMarketAnalysis:
    """
    Fetch and analyse news automatically for the user's market / region label.

    Steps:
      1) Build broad Sri Lanka + agriculture + drought/water queries including the location name.
      2) Pull raw articles via NewsAPI.
      3) Filter non-market noise and classify direct vs indirect evidence.
      4) Extract structured agricultural impact records matching Section 8 format.
      5) Summarise actionable signals for farmers.
    """
    loc = (location or "Sri Lanka").strip()
    queries = [
        f"Sri Lanka drought {loc}",
        f"Sri Lanka vegetable price {loc}",
        f"Sri Lanka food inflation {loc}",
        f"Sri Lanka crop harvest {loc}",
        f"Sri Lanka water shortage agriculture",
        "Sri Lanka drought agriculture",
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
            agricultural_impact_records=[],
            detected_locations=[],
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
            agricultural_impact_records=[],
            detected_locations=[],
        )

    mega_blob = " ".join(blobs)
    direction, topics = _score_direction(mega_blob)
    _, chunks = _parse_titles_and_chunks(filtered)
    joined = " ".join(chunks)

    # Extract structured agricultural records and detected locations
    agri_records, detected_locs = _extract_agricultural_records(filtered)

    # Uncertainty scales with how alarming the language is.
    v_hit = sum(1 for w in ("catastrophic", "collapse", "disaster", "severe drought") if w in joined)
    n_hit = sum(1 for w in ("crisis", "shortage", "strike", "flood", "disease", "water shortage", "heatwave") if w in joined)
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

    # Differentiate direct vs indirect in summary
    has_drought_records = any(r["water_stress"] == "High" for r in agri_records)
    has_indirect_drought = any(r["evidence_type"] == "Indirect agricultural evidence" for r in agri_records)

    if has_drought_records and has_indirect_drought:
        summary = (
            f"News reports indicate agricultural water stress/dry conditions in regions including {', '.join(detected_locs[:3]) or loc}. "
            f"This represents indirect medium-to-long term planting risk rather than an immediate tomato harvest shortage."
        )
    else:
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
        agricultural_impact_records=agri_records,
        detected_locations=detected_locs,
    )
