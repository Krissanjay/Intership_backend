def calculate_profile_match(student_profile, internship):

    score = 0

    # Degree match
    if internship["eligible_degree"]:
        if student_profile["degree"]:
            required_degrees = [d.strip().lower() for d in internship["eligible_degree"].split(',')]
            if student_profile["degree"].strip().lower() in required_degrees:
                score += 50

    # Branch match
    if internship["eligible_branch"]:
        if student_profile["branch"]:
            required_branches = [b.strip().lower() for b in internship["eligible_branch"].split(',')]
            if student_profile["branch"].strip().lower() in required_branches:
                score += 50

    # If no degree/branch restrictions exist
    if not internship["eligible_degree"] and \
       not internship["eligible_branch"]:
        score = 100

    return score