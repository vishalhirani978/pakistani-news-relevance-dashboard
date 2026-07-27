import os
import sqlite3

DB_PATH = "data/raw/processed/database/news.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Articles


def insert_article(article):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO articles(
                    source,
                    headline,
                    image_url,
                    image_path,
                    article_url
                )
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    article.get("source", "Unknown"),
                    article["headline"],
                    article.get("image_url"),
                    article.get("image_path"),
                    article["article_url"],
                ),
            )
        except sqlite3.IntegrityError:
            pass


def insert_articles_batch(articles):
    if not articles:
        return 0
    with get_connection() as conn:
        cursor = conn.cursor()
        count = 0
        for article in articles:
            try:
                cursor.execute(
                    """
                    INSERT INTO articles(
                        source,
                        headline,
                        image_url,
                        image_path,
                        article_url
                    )
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        article.get("source", "Unknown"),
                        article["headline"],
                        article.get("image_url"),
                        article.get("image_path"),
                        article["article_url"],
                    ),
                )
                count += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        return count


def get_all_articles():

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM articles
        """)

        return [dict(row) for row in cursor.fetchall()]


def get_article_by_id(article_id):

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM articles
            WHERE id = ?
        """,
            (article_id,),
        )

        row = cursor.fetchone()

        return dict(row) if row else None


def get_articles_by_source(source):

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM articles
            WHERE source = ?
        """,
            (source,),
        )

        return [dict(row) for row in cursor.fetchall()]


# Statistics


def get_stats():

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM articles
            WHERE LOWER(source)='dawn'
        """)
        dawn_articles = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM articles
            WHERE LOWER(source)='ummat'
        """)
        ummat_articles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM matches")
        total_matches = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM matches
            WHERE match_level='High'
        """)
        high_matches = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM matches
            WHERE match_level='Medium'
        """)
        medium_matches = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM matches
            WHERE match_level='Low'
        """)
        low_matches = cursor.fetchone()[0]

        return {
            "total_articles": total_articles,
            "dawn_articles": dawn_articles,
            "ummat_articles": ummat_articles,
            "total_matches": total_matches,
            "high_matches": high_matches,
            "medium_matches": medium_matches,
            "low_matches": low_matches,
        }


# Matches


def insert_match(match):

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO matches(
                    dawn_id,
                    ummat_id,
                    text_similarity,
                    image_similarity,
                    relevance_score,
                    match_level
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    match["dawn_id"],
                    match["ummat_id"],
                    match["text_similarity"],
                    match["image_similarity"],
                    match["relevance_score"],
                    match["match_level"],
                ),
            )
        except sqlite3.IntegrityError:
            pass


def get_all_matches():

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                m.dawn_id,
                d.headline AS dawn_headline,
                d.image_path AS dawn_image,

                m.ummat_id,
                u.headline AS ummat_headline,
                u.image_path AS ummat_image,

                m.text_similarity,
                m.image_similarity,
                m.relevance_score,
                m.match_level

            FROM matches m

            JOIN articles d
                ON m.dawn_id = d.id

            JOIN articles u
                ON m.ummat_id = u.id

            ORDER BY m.relevance_score DESC
        """)

        rows = []

        for row in cursor.fetchall():
            item = dict(row)

            if item["dawn_image"]:
                item["dawn_image"] = "/images/" + os.path.basename(item["dawn_image"])

            if item["ummat_image"]:
                item["ummat_image"] = "/images/" + os.path.basename(item["ummat_image"])

            rows.append(item)

        return rows
