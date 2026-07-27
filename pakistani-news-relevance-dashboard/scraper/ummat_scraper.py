import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

from backend.crud import insert_articles_batch
from scraper.utils import (
    download_images_parallel,
    translate_urdu_to_english,
    save_translation_cache
)


def fetch_ummat_article_page(art_id, headers):
    url = f"https://ummat.net/{art_id}/"
    try:
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code == 200 and "ummat" in r.text.lower():
            soup = BeautifulSoup(r.text, "html.parser")
            title_elem = soup.find(["h1", "h2"]) or soup.title
            if title_elem:
                h_text = title_elem.get_text(strip=True)
                if h_text and "404" not in h_text and len(h_text) > 5:
                    img_elem = soup.find("img")
                    img_url = None
                    if img_elem:
                        img_url = img_elem.get("src") or img_elem.get("data-src")

                    return {
                        "headline_urdu": h_text,
                        "article_url": url,
                        "image_url": img_url
                    }
    except Exception:
        pass

    return None


def scrape_ummat(target_count=1200):
    """
    High-speed multi-threaded Daily Ummat scraper with translation & parallel image downloads.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }

    categories = [
        "",
        "latest-news/",
        "topnews/",
        "national/",
        "international/",
        "sports/",
        "commerce/",
        "city/",
        "literary/",
        "editorial/"
    ]

    seen_urls = set()
    raw_found = []

    print("Phase 1: Gathering Ummat category section articles...")

    for cat in categories:
        url = f"https://ummat.net/{cat}"
        try:
            response = requests.get(url, headers=headers, timeout=8)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            image_by_url = {}
            for a in soup.find_all("a", href=True):
                img = a.find("img")
                if img:
                    img_url = img.get("src") or img.get("data-src")
                    if img_url:
                        image_by_url.setdefault(a["href"], img_url)

            for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
                link = heading.find("a", href=True)
                if not link:
                    continue

                headline = link.get("title") or link.get("alt") or link.get_text(strip=True)
                article_url = link.get("href")

                if not headline or not article_url:
                    continue

                if article_url in seen_urls:
                    continue

                seen_urls.add(article_url)
                raw_found.append({
                    "headline_urdu": headline,
                    "article_url": article_url,
                    "image_url": image_by_url.get(article_url)
                })

        except Exception:
            continue

    print(f"Category pages yielded {len(raw_found)} distinct articles.")

    # Phase 2: Parallel numeric sequence archive crawl
    if len(raw_found) < target_count:
        latest_id = 991275
        start_id = latest_id
        end_id = max(980000, latest_id - (target_count * 2))
        id_range = list(range(start_id, end_id, -1))

        print(f"Phase 2: Parallel crawling numeric archives ({len(id_range)} IDs)...")

        def _crawl_worker(art_id):
            return fetch_ummat_article_page(art_id, headers)

        with ThreadPoolExecutor(max_workers=30) as executor:
            for result in executor.map(_crawl_worker, id_range):
                if result and result["article_url"] not in seen_urls:
                    seen_urls.add(result["article_url"])
                    raw_found.append(result)
                    if len(raw_found) >= target_count:
                        break

    print(f"\nPhase 3: Translating Urdu headlines & processing {len(raw_found)} Ummat articles...")

    articles = []
    generic_titles = {
        "National", "Health", "Success stories", "Ummat literature",
        "Surprise", "Bam world", "Environmental variation", "Colors of the universe"
    }

    # Parallel translation check
    for idx, item in enumerate(raw_found):
        urdu_text = item["headline_urdu"]
        english_text = translate_urdu_to_english(urdu_text)

        if not english_text or english_text in generic_titles:
            continue

        articles.append({
            "source": "Ummat",
            "headline": english_text,
            "article_url": item["article_url"],
            "image_url": item["image_url"]
        })

    save_translation_cache()

    print(f"\nPhase 4: Downloading images in parallel for {len(articles)} Ummat articles...")

    image_tasks = []
    for idx, item in enumerate(articles):
        if item["image_url"]:
            image_tasks.append((item["image_url"], f"ummat_{idx+1}.webp"))

    downloaded_map = download_images_parallel(image_tasks, max_workers=25)

    final_articles = []
    for item in articles:
        img_url = item["image_url"]
        img_path = downloaded_map.get(img_url) if img_url else None
        final_articles.append({
            "source": "Ummat",
            "headline": item["headline"],
            "article_url": item["article_url"],
            "image_url": img_url,
            "image_path": img_path
        })

    print(f"\nPhase 5: Saving {len(final_articles)} Ummat articles to SQLite database...")
    inserted_count = insert_articles_batch(final_articles)
    print(f"Database insertion completed. New Ummat articles added: {inserted_count}")

    # Export to CSV
    os.makedirs("data/raw", exist_ok=True)
    df = pd.DataFrame(final_articles)
    df.to_csv("data/raw/ummat_articles.csv", index=False, encoding="utf-8-sig")
    print("CSV updated: data/raw/ummat_articles.csv")

    return len(final_articles)


if __name__ == "__main__":
    scrape_ummat()