import json
import os
import time
import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

CACHE_FILE = "data/raw/translation_cache.json"
_translation_cache = {}

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            _translation_cache = json.load(f)
    except Exception:
        _translation_cache = {}


def save_translation_cache():
    os.makedirs("data/raw", exist_ok=True)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_translation_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to save translation cache:", e)


def translate_urdu_to_english(text):
    if not text or not text.strip():
        return text

    clean_text = text.strip()

    if clean_text in _translation_cache:
        return _translation_cache[clean_text]

    if clean_text.isascii():
        _translation_cache[clean_text] = clean_text
        return clean_text

    translated = None
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source="ur", target="en")
        translated = translator.translate(clean_text)
    except Exception:
        translated = None

    if not translated:
        for attempt in range(2):
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=ur&tl=en&dt=t&q={urllib.parse.quote(clean_text)}"
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=4)
                if res.status_code == 200:
                    data = res.json()
                    parts = [item[0] for item in data[0] if item and item[0]]
                    if parts:
                        translated = "".join(parts)
                        break
            except Exception:
                time.sleep(0.2)

    if not translated:
        translated = clean_text

    _translation_cache[clean_text] = translated
    if len(_translation_cache) % 50 == 0:
        save_translation_cache()

    return translated


def download_image(url, filename):
    if not url or url.startswith("data:image"):
        return None

    os.makedirs("data/raw/images", exist_ok=True)
    filepath = f"data/raw/images/{filename}"

    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return filepath

    try:
        response = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            return filepath
    except Exception:
        pass

    return None


def download_images_parallel(image_tasks, max_workers=20):
    """
    image_tasks: list of tuples (url, filename)
    returns: dict mapping url -> filepath
    """
    results = {}

    def _worker(task):
        url, filename = task
        path = download_image(url, filename)
        return url, path

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for url, path in executor.map(_worker, image_tasks):
            results[url] = path

    return results