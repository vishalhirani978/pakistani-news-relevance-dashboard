import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

from backend.crud import insert_articles_batch, get_connection
from scraper.utils import download_images_parallel, translate_urdu_to_english, save_translation_cache
from ml_engine.matcher import match_articles

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def fetch_dawn_page(url):
    articles = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
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

                img = article.find("img")
                img_url = None
                if img:
                    img_url = (
                        img.get("data-src")
                        or img.get("data-lazy-src")
                        or img.get("src")
                    )
                    if img_url and img_url.startswith("//"):
                        img_url = "https:" + img_url
                    if img_url and img_url.startswith("data:"):
                        img_url = None

                articles.append({
                    "headline": headline,
                    "article_url": article_url,
                    "image_url": img_url
                })
    except Exception:
        pass
    return articles


def scrape_dawn_fast(target_count=1200):
    print("=== Scraping Dawn News (English) ===")
    dawn_urls = [f"https://www.dawn.com/latest-news/{p}" for p in range(1, 12)]
    dawn_urls += [
        "https://www.dawn.com/pakistan",
        "https://www.dawn.com/business",
        "https://www.dawn.com/world",
        "https://www.dawn.com/sport",
        "https://www.dawn.com/tech",
        "https://www.dawn.com/opinion"
    ]

    seen = set()
    raw_articles = []

    with ThreadPoolExecutor(max_workers=15) as executor:
        for page_articles in executor.map(fetch_dawn_page, dawn_urls):
            for art in page_articles:
                if art["article_url"] not in seen:
                    seen.add(art["article_url"])
                    raw_articles.append(art)

    print(f"Gathered {len(raw_articles)} distinct Dawn articles.")

    # Parallel image download
    image_tasks = [
        (item["image_url"], f"dawn_{idx+1}.webp")
        for idx, item in enumerate(raw_articles) if item["image_url"]
    ]

    print(f"Downloading {len(image_tasks)} Dawn images in parallel...")
    downloaded_map = download_images_parallel(image_tasks, max_workers=25)

    final_dawn = []
    for item in raw_articles:
        img_url = item["image_url"]
        img_path = downloaded_map.get(img_url) if img_url else None
        final_dawn.append({
            "source": "Dawn",
            "headline": item["headline"],
            "article_url": item["article_url"],
            "image_url": img_url,
            "image_path": img_path
        })

    inserted = insert_articles_batch(final_dawn)
    print(f"Saved {len(final_dawn)} Dawn articles to SQLite news.db (New inserted: {inserted})")

    os.makedirs("data/raw", exist_ok=True)
    pd.DataFrame(final_dawn).to_csv("data/raw/dawn_articles.csv", index=False, encoding="utf-8-sig")
    print("CSV updated: data/raw/dawn_articles.csv\n")
    return len(final_dawn)


def fetch_ummat_page(art_id):
    url = f"https://ummat.net/{art_id}/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=4)
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


def scrape_ummat_fast(target_count=1200):
    print("=== Scraping Daily Ummat (Urdu) ===")

    # Step 1: Category links
    categories = [
        "", "latest-news/", "topnews/", "national/", "international/",
        "sports/", "commerce/", "city/", "literary/", "editorial/"
    ]
    seen = set()
    raw_articles = []

    for cat in categories:
        url = f"https://ummat.net/{cat}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=6)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                img_by_url = {}
                for a in soup.find_all("a", href=True):
                    img = a.find("img")
                    if img:
                        u = img.get("src") or img.get("data-src")
                        if u:
                            img_by_url.setdefault(a["href"], u)

                for h in soup.find_all(["h1", "h2", "h3", "h4"]):
                    link = h.find("a", href=True)
                    if link and link.get("href"):
                        text = link.get("title") or link.get("alt") or link.get_text(strip=True)
                        href = link.get("href")
                        if text and href and href not in seen:
                            seen.add(href)
                            raw_articles.append({
                                "headline_urdu": text,
                                "article_url": href,
                                "image_url": img_by_url.get(href)
                            })
        except Exception:
            pass

    # Step 2: Parallel numeric archive sequence
    latest_id = 991275
    id_range = list(range(latest_id, latest_id - 2500, -1))
    print(f"Checking {len(id_range)} Ummat archive article IDs in parallel...")

    with ThreadPoolExecutor(max_workers=35) as executor:
        for res in executor.map(fetch_ummat_page, id_range):
            if res and res["article_url"] not in seen:
                seen.add(res["article_url"])
                raw_articles.append(res)
                if len(raw_articles) >= target_count:
                    break

    print(f"Gathered {len(raw_articles)} raw Ummat articles.")

    print("Translating Urdu headlines to English with disk caching...")
    final_ummat = []
    generic = {
        "National", "Health", "Success stories", "Ummat literature",
        "Surprise", "Bam world", "Environmental variation", "Colors of the universe"
    }

    for idx, item in enumerate(raw_articles):
        eng = translate_urdu_to_english(item["headline_urdu"])
        if eng and eng not in generic:
            final_ummat.append({
                "source": "Ummat",
                "headline": eng,
                "article_url": item["article_url"],
                "image_url": item["image_url"]
            })

    save_translation_cache()

    # Parallel image download
    image_tasks = [
        (item["image_url"], f"ummat_{idx+1}.webp")
        for idx, item in enumerate(final_ummat) if item["image_url"]
    ]

    print(f"Downloading {len(image_tasks)} Ummat images in parallel...")
    downloaded_map = download_images_parallel(image_tasks, max_workers=25)

    ummat_rows = []
    for item in final_ummat:
        img_url = item["image_url"]
        img_path = downloaded_map.get(img_url) if img_url else None
        ummat_rows.append({
            "source": "Ummat",
            "headline": item["headline"],
            "article_url": item["article_url"],
            "image_url": img_url,
            "image_path": img_path
        })

    inserted = insert_articles_batch(ummat_rows)
    print(f"Saved {len(ummat_rows)} Ummat articles to SQLite news.db (New inserted: {inserted})")

    pd.DataFrame(ummat_rows).to_csv("data/raw/ummat_articles.csv", index=False, encoding="utf-8-sig")
    print("CSV updated: data/raw/ummat_articles.csv\n")
    return len(ummat_rows)


def run_full_pipeline():
    print("==================================================")
    print("STARTING DATASET EXPANSION PIPELINE (DAWN & UMMAT)")
    print("==================================================\n")

    dawn_count = scrape_dawn_fast(target_count=1200)
    ummat_count = scrape_ummat_fast(target_count=1200)

    # Query total DB counts
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT source, COUNT(*) FROM articles GROUP BY source")
        counts = dict(c.fetchall())
        c.execute("SELECT COUNT(*) FROM articles")
        total = c.fetchone()[0]

    print("==================================================")
    print("DATA COLLECTION RESULTS:")
    print(f"  Dawn Articles in DB : {counts.get('Dawn', 0)}")
    print(f"  Ummat Articles in DB: {counts.get('Ummat', 0)}")
    print(f"  TOTAL Articles in DB: {total}")
    print("==================================================\n")

    print("Starting Vectorized Matrix Multimodal Matching Engine...")
    matches = match_articles()
    print(f"Total Matches Found & Recorded in DB: {len(matches)}")


if __name__ == "__main__":
    run_full_pipeline()
