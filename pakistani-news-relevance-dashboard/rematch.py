"""
rematch.py — Clear existing matches and re-run the full matching pipeline
with the updated ML engine (CNN image similarity + revised thresholds).

Run from project root:
    python rematch.py
"""

import sqlite3
import sys
import time

DB_PATH = "data/raw/processed/database/news.db"

def clear_matches():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM matches")
    before = cur.fetchone()[0]
    cur.execute("DELETE FROM matches")
    conn.commit()
    conn.close()
    print(f"Cleared {before} old matches from database.\n")

if __name__ == "__main__":
    print("=" * 60)
    print("STEP 1: Clearing old matches...")
    print("=" * 60)
    clear_matches()

    print("=" * 60)
    print("STEP 2: Running updated matcher (CNN + phash image similarity)...")
    print("=" * 60)
    t0 = time.time()

    from ml_engine.matcher import match_articles
    results = match_articles()

    elapsed = time.time() - t0
    print(f"\nCompleted in {elapsed:.1f}s")
    print(f"Total matches saved: {len(results)}")

    # Quick summary
    levels = {"High": 0, "Medium": 0, "Low": 0}
    for r in results:
        levels[r["level"]] += 1

    print("\n=== MATCH LEVEL SUMMARY ===")
    for lvl, cnt in levels.items():
        pct = cnt / max(len(results), 1) * 100
        print(f"  {lvl:<8}: {cnt:>3}  ({pct:>5.1f}%)")

    print("\nTop 10 matches:")
    for r in results[:10]:
        print(f"  [{r['level']:<6}] score={r['score']:.3f}  "
              f"text={r['details']['text_similarity']:.3f}  "
              f"img={r['details']['image_similarity']:.3f}")
        print(f"    Dawn : {r['dawn_headline'][:65]}")
        print(f"    Ummat: {r['ummat_headline'][:65]}")
        print()
