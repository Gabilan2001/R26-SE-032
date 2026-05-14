from pydantic import BaseModel


class NewsResponse(BaseModel):
    query: str
    sentiment: str
    uncertainty_level: str
    headline_summary: str
    news_score: float
