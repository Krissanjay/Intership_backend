from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer(
    "all-MiniLM-L6-v2",
    device="cpu"
)


def calculate_semantic_score(resume_text, internship_description):
    if not resume_text or not internship_description:
        return 0.0

    embeddings = model.encode(
        [resume_text, internship_description],
        batch_size=2,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    score = float(similarity) * 100
    return round(score, 2)