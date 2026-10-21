"""Structured output from automatic agriculture / market news analysis."""

from typing import List

from pydantic import BaseModel, Field


class NewsMarketAnalysis(BaseModel):
    """
    Tomato-relevant news signals derived from NewsAPI articles (no user query).

    `price_impact_direction` is a simple heuristic for supply/demand pressure.
    """

    price_impact_direction: str = Field(
        ...,
        description="increase | decrease | neutral | uncertain",
    )
    market_impact_summary: str = Field(..., description="Short farmer-friendly summary.")
    matched_topics: List[str] = Field(
        default_factory=list,
        description="Detected themes (e.g. flood, strike, inflation).",
    )
    relevant_headlines: List[str] = Field(default_factory=list, description="Filtered headlines.")
    articles_analyzed: int = Field(0, ge=0)
    uncertainty_level: str = Field("moderate", description="low | moderate | elevated | very_high")
    news_sentiment: str = Field(
        "neutral",
        description="Maps to confidence blending: positive | neutral | negative | very_negative",
    )
    news_score: float = Field(0.55, ge=0.0, le=1.0)
    data_source: str = Field("NewsAPI.org", description="API label or no-results / fallback.")
    agricultural_impact_records: List[dict] = Field(
        default_factory=list,
        description="Structured agricultural impact records (location, evidence type, water/heat stress, time horizon).",
    )
    detected_locations: List[str] = Field(
        default_factory=list,
        description="Agricultural locations recognized in the news (e.g. Anuradhapura, Badulla, Dambulla).",
    )
