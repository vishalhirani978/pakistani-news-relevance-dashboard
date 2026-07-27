import time
import schedule

from scraper.dawn_scraper import scrape_dawn
from scraper.ummat_scraper import scrape_ummat


def scrape_all():

    print("\n========== Starting Scraping ==========\n")

    try:
        scrape_dawn()
        print("\nDawn scraping completed.\n")

    except Exception as e:
        print(f"\nDawn scraper failed: {e}\n")

    try:
        scrape_ummat()
        print("\nUmmat scraping completed.\n")

    except Exception as e:
        print(f"\nUmmat scraper failed: {e}\n")

    print("========== Scraping Finished ==========\n")


schedule.every(6).hours.do(scrape_all)

print("Scheduler started...")

scrape_all()

while True:
    schedule.run_pending()
    time.sleep(60)