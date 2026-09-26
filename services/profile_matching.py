def calculate_profile_match(student_profile, internship):

    score = 0

    # Degree match
    if internship["eligible_degree"]:
        if student_profile["degree"] and \
           internship["eligible_degree"].lower() in \
           student_profile["degree"].lower():
            score += 50

    # Branch match
    if internship["eligible_branch"]:
        if student_profile["branch"] and \
           internship["eligible_branch"].lower() in \
           student_profile["branch"].lower():
            score += 50

    # If no degree/branch restrictions exist
    if not internship["eligible_degree"] and \
       not internship["eligible_branch"]:
        score = 100

    return score