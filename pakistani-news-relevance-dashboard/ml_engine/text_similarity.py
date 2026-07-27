from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ml_engine.preprocessing import preprocess_text

model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_text_similarity(text1, text2):
    """
    Calculate semantic similarity between two headlines.
    """

    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)

    embedding1 = model.encode([text1])
    embedding2 = model.encode([text2])

    similarity = cosine_similarity(
        embedding1,
        embedding2
    )[0][0]

    return round(float(similarity), 3)