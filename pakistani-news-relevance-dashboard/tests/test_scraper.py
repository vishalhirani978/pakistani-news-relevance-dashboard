import os
import sqlite3

current_dir = os.path.dirname(os.path.abspath(__file__))

project_root = os.path.dirname(current_dir)

db_path = os.path.join(project_root, "data", "raw", "processed", "database", "news.db")

os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)

print("Successful")
