import sqlite3

conn = sqlite3.connect("data/raw/processed/database/news.db")
cursor = conn.cursor()

cursor.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS idx_match
ON matches(dawn_id, ummat_id);
""")

conn.commit()
conn.close()

print("Unique index created.")