import sqlite3
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

from backend.crud import insert_match
from ml_engine.text_similarity import model
from ml_engine.preprocessing import preprocess_text
from ml_engine.image_similarity import calculate_image_similarity

DATABASE = "data/raw/processed/database/news.db"

# Match-level thresholds
HIGH_THRESHOLD = 0.50
MEDIUM_THRESHOLD = 0.38

# Filters & weights (tuned for cross-language matching with translation)
MIN_TEXT_FILTER = 0.20
MIN_TEXT_SAVE = 0.25
MIN_SCORE_SAVE = 0.30

TEXT_WEIGHT = 0.65
IMAGE_WEIGHT = 0.35


def match_articles():
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found!")
        return []

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Fetch Dawn articles
    cursor.execute("""
        SELECT id, headline, image_path
        FROM articles
        WHERE LOWER(source) = 'dawn'
    """)
    dawn_articles = cursor.fetchall()

    # Fetch Ummat articles
    cursor.execute("""
        SELECT id, headline, image_path
        FROM articles
        WHERE LOWER(source) = 'ummat'
    """)
    ummat_articles = cursor.fetchall()

    conn.close()

    if not dawn_articles or not ummat_articles:
        print("Not enough articles to run matching engine.")
        print(f"Dawn: {len(dawn_articles)}, Ummat: {len(ummat_articles)}")
        return []

    generic = {
        "National",
        "Health",
        "Success stories",
        "Ummat literature",
        "Surprise",
        "Bam world",
        "Environmental variation",
        "Colors of the universe",
    }

    print("==========================================")
    print(f"Dawn Articles : {len(dawn_articles)}")
    print(f"Ummat Articles: {len(ummat_articles)}")
    print("==========================================\n")

    print("Step 1: Batch pre-processing & embedding headlines...")
    dawn_clean = [preprocess_text(d[1]) for d in dawn_articles]
    ummat_clean = [preprocess_text(u[1]) for u in ummat_articles]

    dawn_embeddings = model.encode(dawn_clean, show_progress_bar=True, batch_size=64)
    ummat_embeddings = model.encode(ummat_clean, show_progress_bar=True, batch_size=64)

    print("\nStep 2: Vectorized Matrix Cosine Similarity computation...")
    sim_matrix = cosine_similarity(dawn_embeddings, ummat_embeddings)
    print(f"Similarity matrix calculated: shape {sim_matrix.shape}")

    print("\nStep 3: Evaluating candidate article pairs...")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    best_matches = []
    inserted_matches = 0
    MAX_IMAGE_CANDIDATES = 5

    for idx_d, dawn in enumerate(dawn_articles):
        dawn_id, dawn_headline, dawn_img = dawn

        candidate_indices = np.where(sim_matrix[idx_d] >= MIN_TEXT_FILTER)[0]

        # Filter out generic headlines first
        filtered_indices = []
        for idx_u in candidate_indices:
            ummat_headline = ummat_articles[idx_u][1]
            if ummat_headline.strip() not in generic:
                filtered_indices.append(idx_u)

        if not filtered_indices:
            continue

        # Rank by text similarity, only compute image sim for top N
        text_sims = [
            (idx_u, float(sim_matrix[idx_d, idx_u])) for idx_u in filtered_indices
        ]
        text_sims.sort(key=lambda x: x[1], reverse=True)
        top_candidates = text_sims[:MAX_IMAGE_CANDIDATES]

        best_score = -1.0
        best_u_idx = None
        best_result = None

        for idx_u, text_sim_raw in top_candidates:
            ummat = ummat_articles[idx_u]
            ummat_id, ummat_headline, ummat_img = ummat

            text_sim = round(max(0.0, text_sim_raw), 3)

            image_sim = 0.0
            if (
                dawn_img
                and ummat_img
                and os.path.exists(dawn_img)
                and os.path.exists(ummat_img)
            ):
                try:
                    image_sim = calculate_image_similarity(dawn_img, ummat_img)
                except Exception:
                    image_sim = 0.0

            relevance_score = round(
                TEXT_WEIGHT * text_sim + IMAGE_WEIGHT * image_sim, 3
            )

            if relevance_score > best_score:
                best_score = relevance_score
                best_u_idx = idx_u
                best_result = {
                    "text_similarity": text_sim,
                    "image_similarity": image_sim,
                    "relevance_score": relevance_score,
                }

        if best_u_idx is not None and best_result is not None:
            if (
                best_result["text_similarity"] >= MIN_TEXT_SAVE
                and best_score >= MIN_SCORE_SAVE
            ):
                best_u = ummat_articles[best_u_idx]

                if best_score >= HIGH_THRESHOLD:
                    level = "High"
                elif best_score >= MEDIUM_THRESHOLD:
                    level = "Medium"
                else:
                    level = "Low"

                # Check duplicate
                cursor.execute(
                    """
                    SELECT id FROM matches WHERE dawn_id = ? AND ummat_id = ?
                """,
                    (dawn_id, best_u[0]),
                )

                if not cursor.fetchone():
                    insert_match(
                        {
                            "dawn_id": dawn_id,
                            "ummat_id": best_u[0],
                            "text_similarity": best_result["text_similarity"],
                            "image_similarity": best_result["image_similarity"],
                            "relevance_score": best_result["relevance_score"],
                            "match_level": level,
                        }
                    )
                    inserted_matches += 1

                best_matches.append(
                    {
                        "dawn_id": dawn_id,
                        "dawn_headline": dawn_headline,
                        "ummat_id": best_u[0],
                        "ummat_headline": best_u[1],
                        "score": best_score,
                        "level": level,
                        "details": {
                            "text_similarity": best_result["text_similarity"],
                            "image_similarity": best_result["image_similarity"],
                            "relevance_score": best_result["relevance_score"],
                        },
                    }
                )

    conn.close()

    best_matches.sort(key=lambda x: x["score"], reverse=True)
    print("\nMatching Completed Successfully!")
    print(
        f"Total Relevant Matches Recorded: {len(best_matches)} (New inserted: {inserted_matches})"
    )

    return best_matches


if __name__ == "__main__":
    match_articles()
