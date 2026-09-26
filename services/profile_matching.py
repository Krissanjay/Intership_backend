import re

def normalize_string(s):
    if not s: return ""
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

def calculate_profile_match(student_profile, internship):
    total_criteria = 0
    matched_criteria = 0

    # Degree match
    if internship.get("eligible_degree"):
        total_criteria += 1
        if student_profile.get("degree"):
            required_degrees = [normalize_string(d) for d in internship["eligible_degree"].split(',')]
            if normalize_string(student_profile["degree"]) in required_degrees:
                matched_criteria += 1

    # Branch match
    if internship.get("eligible_branch"):
        total_criteria += 1
        if student_profile.get("branch"):
            required_branches = [normalize_string(b) for b in internship["eligible_branch"].split(',')]
            if normalize_string(student_profile["branch"]) in required_branches:
                matched_criteria += 1

    # If no degree/branch restrictions exist
    if total_criteria == 0:
        return 100

    return int((matched_criteria / total_criteria) * 100)