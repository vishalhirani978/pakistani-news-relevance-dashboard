from backend.crud import get_all_articles

articles = get_all_articles()

for article in articles[:5]:
    print(article)