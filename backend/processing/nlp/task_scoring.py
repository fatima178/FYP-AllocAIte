"""Helpers for computing task matching scores and explanations."""

# scale experience 0–1 based on max value
def normalize_experience(experience, max_experience):
    if not max_experience:
        return 0.0
    safe_exp = experience or 0
    return max(0.0, safe_exp / max_experience)


# quick role relevance check using text overlap
def compute_role_match(task_description, role):
    if not role:
        return 0.0

    td = task_description.lower()
    role_lower = role.lower()

    # full phrase match
    if role_lower in td:
        return 1.0

    # partial word match
    for word in role_lower.split():
        if word and word in td:
            return 0.6

    # default low relevance
    return 0.3


# choose weights depending on whether skills matched
def _determine_weights(skill_score):
    # if skills matched more weight to skills + experience
    if skill_score > 0:
        return 0.30, 0.30, 0.20, 0.10, 0.10
    # if no skill match more weight to semantic + experience
    return 0.30, 0.10, 0.35, 0.15, 0.10


# convert availability % into a simple text label
def _availability_label(percent):
    if percent >= 70:
        return "High availability"
    if percent >= 40:
        return "Partial availability"
    return "Limited availability"


# create short natural explanation for user
def _build_reason(skills, role_score, role, experience, availability_percent):
    explanation = []

    # skills summary
    if skills:
        explanation.append(f"Direct skill matches: {', '.join(skills)}")
    else:
        explanation.append("No direct skill overlap with this task")

    # role relevance summary
    if role_score >= 0.8:
        explanation.append(f"Role as {role} fits the task directly")
    elif role_score >= 0.5:
        explanation.append(f"Role as {role} is related to the task")
    else:
        explanation.append(f"Role as {role} provides partial relevance")

    # experience note
    if experience >= 5:
        explanation.append(f"Strong experience ({experience} years)")
    else:
        explanation.append(f"{experience} years of experience")

    # availability note
    if availability_percent >= 70:
        explanation.append("Fully available during the required timeframe")
    elif availability_percent >= 40:
        explanation.append("Partially available during the timeframe")
    else:
        explanation.append("Availability is limited for this period")

    return ". ".join(explanation) + "."


# build final dict for the ranked employee entry
def build_recommendation_entry(
    employee,
    semantic_score,
    skill_score,
    experience_score,
    role_score,
    availability_score,
    matched_skills,
):
    # decide which weights to use
    (
        weight_semantic,
        weight_skill,
        weight_experience,
        weight_role,
        weight_availability,
    ) = _determine_weights(skill_score)

    # weighted score calculation
    final_score = (
        weight_semantic * semantic_score +
        weight_skill * skill_score +
        weight_experience * experience_score +
        weight_role * role_score +
        weight_availability * availability_score
    )

    # convert to readable %
    score_percent = max(0, min(100, round(final_score * 100)))
    availability_percent = max(0, min(100, round(availability_score * 100)))
    availability_label = _availability_label(availability_percent)

    # build explanation text
    reason = _build_reason(
        matched_skills,
        role_score,
        employee["role"],
        employee["experience"],
        availability_percent,
    )

    # packaged result for frontend
    return {
        "employee_id": employee["employee_id"],
        "name": employee["name"],
        "role": employee["role"],
        "score_percent": score_percent,
        "availability_percent": availability_percent,
        "availability_label": availability_label,
        "skills": matched_skills,
        "reason": reason,
        "final_score": final_score,
    }
