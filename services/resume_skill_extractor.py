import re


def extract_skills(text, available_skills):
    if not text:
        return []

    text = text.lower()

    detected_skills = []

    for skill in available_skills:
        skill_name = skill["skill_name"].lower()

        # Escape special regex characters
        pattern = re.escape(skill_name)

        # Match the skill anywhere in the resume
        if re.search(pattern, text, re.IGNORECASE):
            detected_skills.append(skill_name)

    return detected_skills