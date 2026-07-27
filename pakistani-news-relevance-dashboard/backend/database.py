import sqlite3
import os

DB_PATH = "data/raw/processed/database/news.db"

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Articles Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS articles(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    headline TEXT,
    image_url TEXT,
    image_path TEXT,
    article_url TEXT UNIQUE,
    published_at TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score REAL,
    label TEXT
)
""")

# Matches Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS matches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    dawn_id INTEGER NOT NULL,
    ummat_id INTEGER NOT NULL,

    text_similarity REAL,
    image_similarity REAL,
    relevance_score REAL,

    match_level TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(dawn_id) REFERENCES articles(id),
    FOREIGN KEY(ummat_id) REFERENCES articles(id)
)
""")

conn.commit()
conn.close()

print("Database initialized successfully.")