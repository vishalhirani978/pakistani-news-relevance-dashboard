from fastapi import APIRouter, HTTPException
from backend.crud import get_all_articles, get_article_by_id

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get("/")
def articles():
    return get_all_articles()


@router.get("/{article_id}")
def article(article_id: int):

    article = get_article_by_id(article_id)

    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return article
