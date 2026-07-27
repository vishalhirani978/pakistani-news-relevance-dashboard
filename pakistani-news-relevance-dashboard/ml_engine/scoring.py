from ml_engine.text_similarity import calculate_text_similarity
from ml_engine.image_similarity import calculate_image_similarity


def calculate_relevance(
    headline1: str,
    headline2: str,
    image1_path: str,
    image2_path: str,
    text_weight: float = 0.65,
    image_weight: float = 0.35,
) -> dict:
    """
    Calculate overall relevance score between two news articles.

    Weights:
      - text_weight  : 0.65  — semantic headline similarity (Sentence Transformers)
      - image_weight : 0.35  — visual content similarity (dhash + HSV histogram)
    """

    text_score = calculate_text_similarity(headline1, headline2)

    image_score = calculate_image_similarity(image1_path, image2_path)

    relevance = text_weight * text_score + image_weight * image_score

    return {
        "text_similarity": round(text_score, 3),
        "image_similarity": round(image_score, 3),
        "relevance_score": round(relevance, 3),
    }
