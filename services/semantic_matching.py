
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def calculate_semantic_score(resume_text, internship_description):

    if not resume_text or not internship_description:
        return 0.0

    model = get_model()

    embeddings = model.encode([
        resume_text,
        internship_description
    ])

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    score = max(0.0, float(similarity)) * 100

    return round(score, 2)
