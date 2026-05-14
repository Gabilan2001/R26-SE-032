from app.schemas.news_schema import NewsResponse


def analyze_market_news(query: str) -> NewsResponse:
    """Analyze market news and return uncertainty and sentiment signals."""
    # Placeholder for future news API integration and sentiment analysis.
    return NewsResponse(
        query=query,
        sentiment="neutral",
        uncertainty_level="elevated",
        headline_summary="Local market prices remain stable despite supply uncertainty.",
        news_score=0.58,
    )
