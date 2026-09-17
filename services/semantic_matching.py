from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_semantic_score(resume_text, internship_description):

    if not resume_text or not internship_description:
        return 0.0

    resume_embedding = model.encode(
        [resume_text]
    )

    internship_embedding = model.encode(
        [internship_description]
    )

    similarity = cosine_similarity(
        resume_embedding,
        internship_embedding
    )[0][0]

    # Convert NumPy float32 to normal Python float
    score = float(similarity) * 100

    return round(score, 2)