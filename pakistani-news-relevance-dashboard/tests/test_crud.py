from backend.crud import (
    get_all_articles,
    get_article_by_id,
    get_stats
)

print("All Articles:")
print(get_all_articles()[:3])

print("\nArticle ID 1:")
print(get_article_by_id(1))

print("\nStats:")
print(get_stats())