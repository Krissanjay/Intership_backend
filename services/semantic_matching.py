from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_semantic_score(resume_text, internship_description):
    if not resume_text or not internship_description:
        return 0.0

    documents = [
        str(resume_text),
        str(internship_description)
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000
    )

    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:2]
    )[0][0]

    score = float(similarity) * 100

    return round(score, 2)