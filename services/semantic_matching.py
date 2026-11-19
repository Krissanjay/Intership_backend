
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model once when the application starts
model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_semantic_score(resume_text, internship_description):

    if not resume_text or not internship_description:
        return 0.0

    resume_text = str(resume_text).strip()
    internship_description = str(internship_description).strip()

    if not resume_text or not internship_description:
        return 0.0

    embeddings = model.encode([
        resume_text,
        internship_description
    ])

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    # Convert similarity to percentage
    score = max(0.0, float(similarity)) * 100

    return round(score, 2)
