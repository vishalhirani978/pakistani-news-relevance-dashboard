from pydantic import BaseModel
from typing import Optional

# Articles


class Article(BaseModel):
    id: int
    source: str
    headline: str
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    article_url: str
    published_at: Optional[str] = None
    scraped_at: Optional[str] = None
    score: Optional[float] = None
    label: Optional[str] = None


# Statistics


class Stats(BaseModel):
    total_articles: int
    dawn_articles: int
    ummat_articles: int

    total_matches: int

    high_matches: int
    medium_matches: int
    low_matches: int


# Matches


class MatchResponse(BaseModel):
    dawn_id: int
    dawn_headline: str
    dawn_image: Optional[str] = None

    ummat_id: int
    ummat_headline: str
    ummat_image: Optional[str] = None

    text_similarity: float
    image_similarity: float
    relevance_score: float
    match_level: str
