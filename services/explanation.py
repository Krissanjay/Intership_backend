def generate_explanation(
    overall_score,
    skill_match_score,
    semantic_score,
    profile_match_score,
    matched_skills,
    missing_skills
):

    matched_names = [
        skill["skill_name"]
        for skill in matched_skills
    ]

    missing_names = [
        skill["skill_name"]
        for skill in missing_skills
    ]

    explanation_parts = []

    if skill_match_score >= 80:
        explanation_parts.append(
            "Your skills strongly match the internship requirements."
        )
    elif skill_match_score >= 50:
        explanation_parts.append(
            "Your skills partially match the internship requirements."
        )
    else:
        explanation_parts.append(
            "Your current skills have a limited match with the internship."
        )

    if semantic_score >= 70:
        explanation_parts.append(
            "Your resume content is highly relevant to the internship description."
        )
    elif semantic_score >= 40:
        explanation_parts.append(
            "Your resume has moderate relevance to the internship description."
        )
    else:
        explanation_parts.append(
            "Your resume has relatively low semantic similarity with the internship."
        )

    if profile_match_score >= 80:
        explanation_parts.append(
            "Your academic profile matches the internship requirements well."
        )
    elif profile_match_score >= 50:
        explanation_parts.append(
            "Your academic profile partially matches the internship."
        )

    if matched_names:
        explanation_parts.append(
            "Matched skills: " + ", ".join(matched_names) + "."
        )

    explanation = " ".join(explanation_parts)

    if missing_names:
        skill_gap = (
            "Skills to improve: "
            + ", ".join(missing_names)
            + "."
        )
    else:
        skill_gap = "No major required skill gaps detected."

    return {
        "explanation": explanation,
        "skill_gap": skill_gap
    }