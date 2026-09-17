def calculate_skill_match(student_skills, internship_skills):

    student_skill_ids = set()

    for skill in student_skills:
        student_skill_ids.add(skill["skill_id"])

    total_weight = 0
    matched_weight = 0

    matched_skills = []
    missing_skills = []

    # Importance weights
    weights = {
        "High": 3,
        "Medium": 2,
        "Low": 1
    }

    for skill in internship_skills:

        skill_id = skill["skill_id"]
        skill_name = skill["skill_name"]
        importance = skill["importance"]

        weight = weights.get(importance, 1)

        total_weight += weight

        if skill_id in student_skill_ids:

            matched_weight += weight

            matched_skills.append({
                "skill_id": skill_id,
                "skill_name": skill_name,
                "importance": importance
            })

        else:

            missing_skills.append({
                "skill_id": skill_id,
                "skill_name": skill_name,
                "importance": importance
            })

    if total_weight == 0:
        score = 0
    else:
        score = (matched_weight / total_weight) * 100

    return {
        "score": round(score, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }