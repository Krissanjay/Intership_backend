import re

def normalize_string(s):
    if not s: return ""
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

def calculate_profile_match(student_profile, internship):

    score = 0

    # Degree match
    if internship["eligible_degree"]:
        if student_profile["degree"]:
            required_degrees = [normalize_string(d) for d in internship["eligible_degree"].split(',')]
            if normalize_string(student_profile["degree"]) in required_degrees:
                score += 50

    # Branch match
    if internship["eligible_branch"]:
        if student_profile["branch"]:
            required_branches = [normalize_string(b) for b in internship["eligible_branch"].split(',')]
            if normalize_string(student_profile["branch"]) in required_branches:
                score += 50

    # If no degree/branch restrictions exist
    if not internship["eligible_degree"] and \
       not internship["eligible_branch"]:
        score = 100

    return score