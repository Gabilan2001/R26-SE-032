from typing import List

from pydantic import BaseModel, Field


class NewsResponse(BaseModel):
    """Structured news insight for market uncertainty (NewsAPI.org when configured)."""

    query: str
    sentiment: str = Field(
        ...,
        description="positive | neutral | negative | very_negative (heuristic from headlines)",
    )
    uncertainty_level: str = Field(
        ...,
        description="low | moderate | elevated | very_high — derived from tone and volume",
    )
    headline_summary: str
    news_score: float = Field(..., ge=0.0, le=1.0, description="Higher usually means calmer / more stable tone.")
    data_source: str = Field(
        "fallback",
        description="NewsAPI.org when articles exist; NewsAPI.org (no results) if empty; fallback on errors.",
    )
    headlines: List[str] = Field(default_factory=list, description="Up to a few recent headlines.")
    total_articles: int = Field(0, description="Articles returned in this response batch.")
