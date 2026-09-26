import re

def normalize_string(s):
    if not s: return ""
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

def check_eligibility(student_profile, internship):

    reasons = []
    eligible = True

    # CGPA check
    if internship["minimum_cgpa"] is not None:

        student_cgpa = student_profile["cgpa"]
        minimum_cgpa = internship["minimum_cgpa"]

        if student_cgpa is None:
            eligible = False
            reasons.append("CGPA not provided")

        elif float(student_cgpa) < float(minimum_cgpa):
            eligible = False
            reasons.append(
                f"CGPA below required minimum of {minimum_cgpa}"
            )

    # Degree check
    if internship["eligible_degree"]:

        required_degrees = [normalize_string(d) for d in internship["eligible_degree"].split(',')]
        
        if student_profile["degree"]:
            student_degree = normalize_string(student_profile["degree"])
            if student_degree not in required_degrees:
                eligible = False
                reasons.append(
                    f"Degree requirement: {internship['eligible_degree']}"
                )
        else:
            eligible = False
            reasons.append(
                f"Degree requirement: {internship['eligible_degree']}"
            )

    # Branch check
    if internship["eligible_branch"]:

        required_branches = [normalize_string(b) for b in internship["eligible_branch"].split(',')]
        
        if student_profile["branch"]:
            student_branch = normalize_string(student_profile["branch"])
            if student_branch not in required_branches:
                eligible = False
                reasons.append(
                    f"Branch requirement: {internship['eligible_branch']}"
                )
        else:
            eligible = False
            reasons.append(
                f"Branch requirement: {internship['eligible_branch']}"
            )

    if eligible:
        reasons.append("Student satisfies all configured eligibility criteria")

    return {
        "eligible": eligible,
        "reasons": reasons
    }