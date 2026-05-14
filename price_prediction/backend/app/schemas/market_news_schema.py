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
