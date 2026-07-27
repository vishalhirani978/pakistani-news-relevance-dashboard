from backend.crud import (
    get_all_articles,
    get_article_by_id,
    get_articles_by_source,
    get_stats
)


print("\n===== ALL ARTICLES =====")
articles = get_all_articles()
print(f"Total: {len(articles)}")
print(articles[:3])


print("\n===== ARTICLE ID 1 =====")
print(get_article_by_id(1))


print("\n===== DAWN ARTICLES =====")
dawn_articles = get_articles_by_source("Dawn")
print(f"Total Dawn Articles: {len(dawn_articles)}")


print("\n===== STATS =====")
print(get_stats())