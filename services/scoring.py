def calculate_overall_score(
    skill_match_score,
    semantic_score,
    profile_match_score
):

    overall_score = (
        (skill_match_score * 0.35)
        + (semantic_score * 0.35)
        + (profile_match_score * 0.30)
    )

    return round(overall_score, 2)