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

        required_degree = internship["eligible_degree"].strip().lower()
        
        if student_profile["degree"]:
            student_degree = student_profile["degree"].strip().lower()
            if required_degree not in student_degree:
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

        required_branch = internship["eligible_branch"].strip().lower()
        
        if student_profile["branch"]:
            student_branch = student_profile["branch"].strip().lower()
            if required_branch not in student_branch:
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