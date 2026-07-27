import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

from backend.crud import insert_articles_batch
from scraper.utils import download_images_parallel


def scrape_dawn(max_pages_per_section=10):
    """
    High-speed multi-threaded Dawn scraper for 1000+ real news articles.
    """
    sections = [
        "latest-news",
        "pakistan",
        "business",
        "world",
        "sport",
        "tech",
        "opinion",
        "culture",
        "prism"
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }

    seen_urls = set()
    raw_articles = []

    print(f"Phase 1: Gathering Dawn articles across {len(sections)} sections...")

    for section in sections:
        for page in range(1, max_pages_per_section + 1):
            url = f"https://www.dawn.com/{section}" if page == 1 else f"https://www.dawn.com/{section}/{page}"
            try:
                res = requests.get(url, headers=headers, timeout=8)
                if res.status_code != 200:
                    continue

                soup = BeautifulSoup(res.text, "html.parser")
                for article in soup.find_all("article", class_="story"):
                    link = article.find("a", href=True)
                    if not link:
                        continue

                    headline = (
                        link.get("title")
                        or link.get("alt")
                        or link.get_text(strip=True)
                    )
                    article_url = link.get("href")

                    if not headline or not article_url:
                        continue

                    if article_url.startswith("//"):
                        article_url = "https:" + article_url
                    elif article_url.startswith("/"):
                        article_url = "https://www.dawn.com" + article_url

                    if article_url in seen_urls:
                        continue

                    seen_urls.add(article_url)

                    image = article.find("img")
                    image_url = None
                    if image:
                        image_url = (
                            image.get("data-src")
                            or image.get("data-lazy-src")
                            or image.get("src")
                        )
                        if image_url and image_url.startswith("//"):
                            image_url = "https:" + image_url
                        if image_url and image_url.startswith("data:"):
                            image_url = None

                    raw_articles.append({
                        "source": "Dawn",
                        "headline": headline,
                        "article_url": article_url,
                        "image_url": image_url
                    })

            except Exception as e:
                continue

        print(f"  Section '{section}' harvested. Total collected: {len(raw_articles)}")

    print(f"\nPhase 2: Downloading images in parallel for {len(raw_articles)} articles...")

    image_tasks = []
    for idx, item in enumerate(raw_articles):
        if item["image_url"]:
            image_tasks.append((item["image_url"], f"dawn_{idx+1}.webp"))

    downloaded_map = download_images_parallel(image_tasks, max_workers=25)

    articles = []
    for item in raw_articles:
        img_url = item["image_url"]
        img_path = downloaded_map.get(img_url) if img_url else None
        articles.append({
            "source": "Dawn",
            "headline": item["headline"],
            "article_url": item["article_url"],
            "image_url": img_url,
            "image_path": img_path
        })

    print(f"Phase 3: Saving {len(articles)} Dawn articles to SQLite database...")
    inserted_count = insert_articles_batch(articles)
    print(f"Database insertion completed. New articles added: {inserted_count}")

    # Save to CSV
    os.makedirs("data/raw", exist_ok=True)
    df = pd.DataFrame(articles)
    df.to_csv("data/raw/dawn_articles.csv", index=False, encoding="utf-8-sig")
    print("CSV updated: data/raw/dawn_articles.csv")

    return len(articles)


if __name__ == "__main__":
    scrape_dawn()