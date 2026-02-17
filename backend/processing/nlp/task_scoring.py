"""helpers for computing task matching scores and explanations."""

# ----------------------------------------------------------
# experience normalisation
# ----------------------------------------------------------
# converts experience years into a 0–1 scale so it can be
# combined fairly with other metrics. this prevents someone
# with huge years of experience from dominating the score.
def normalize_experience(experience, max_experience):
    if not max_experience:
        return 0.0
    safe_exp = experience or 0
    return max(0.0, safe_exp / max_experience)


# ----------------------------------------------------------
# role relevance scoring
# ----------------------------------------------------------
# checks how strongly the employee's role name relates to
# the task description. this is intentionally lightweight and
# meant to complement semantic similarity rather than replace it.
def compute_role_match(task_description, role):
    if not role:
        return 0.0

    td = task_description.lower()
    role_lower = role.lower()

    # strongest match: full role phrase appears in task text
    if role_lower in td:
        return 1.0

    # medium match: any individual word overlaps
    for word in role_lower.split():
        if word and word in td:
            return 0.6

    # default low relevance when nothing overlaps
    return 0.3


# ----------------------------------------------------------
# weighting strategy
# ----------------------------------------------------------
# chooses how much each metric should influence the final score.
# this changes depending on whether the employee actually had any skill matches.
# if skills matched: skill + experience become more important
# if no skills matched: semantic + experience dominate
def _determine_weights(skill_score):
    if skill_score > 0:
        # skills matched: emphasize skills + experience
        return 0.28, 0.30, 0.20, 0.10, 0.07, 0.05
    # no skill match: emphasize semantic understanding
    return 0.33, 0.10, 0.20, 0.15, 0.17, 0.05


# ----------------------------------------------------------
# availability readability helper
# ----------------------------------------------------------
# converts a numeric % availability into a human-friendly label.
def _availability_label(percent):
    if percent >= 70:
        return "High availability"
    if percent >= 40:
        return "Partial availability"
    return "Limited availability"


# ----------------------------------------------------------
# construct natural sounding explanatory text
# ----------------------------------------------------------
# produces a short, human readable explanation summarising:
#   - skill matches
#   - role relevance
#   - experience level
#   - availability
def _build_reason(skills, goals, role_score, role, experience, availability_percent, workload_score):
    explanation = []

    # skills summary
    if skills:
        explanation.append(f"Direct skill matches: {', '.join(skills)}")
    else:
        explanation.append("No direct skill overlap with this task")

    # learning goals summary
    if goals:
        explanation.append(f"Learning goals aligned: {', '.join(goals)}")

    # role relevance summary
    if role_score >= 0.8:
        explanation.append(f"Role as {role} fits the task directly")
    elif role_score >= 0.5:
        explanation.append(f"Role as {role} is related to the task")
    else:
        explanation.append(f"Role as {role} provides partial relevance")

    # experience summary
    if experience >= 5:
        explanation.append(f"Strong experience ({experience} years)")
    else:
        explanation.append(f"{experience} years of experience")

    # availability summary
    if availability_percent >= 70:
        explanation.append("Fully available during the required timeframe")
    elif availability_percent >= 40:
        explanation.append("Partially available during the timeframe")
    else:
        explanation.append("Availability is limited for this period")

    # fairness summary
    if workload_score >= 0.75:
        explanation.append("Recent workload is lighter than average")
    elif workload_score >= 0.45:
        explanation.append("Recent workload is balanced")
    else:
        explanation.append("Recent workload is heavier than average")

    return ". ".join(explanation) + "."


# ----------------------------------------------------------
# build final recommendation record
# ----------------------------------------------------------
# constructs the complete result dictionary for one employee,
# including:
#   - all individual scores
#   - weighted final score
#   - readable percentages
#   - labels
#   - explanation for the user
def build_recommendation_entry(
    employee,
    semantic_score,
    skill_score,
    experience_score,
    role_score,
    availability_score,
    matched_skills,
    matched_goals,
    workload_score,
):
    # choose weighting strategy based on skill match outcome
    (
        weight_semantic,
        weight_skill,
        weight_experience,
        weight_role,
        weight_availability,
        weight_fairness,
    ) = _determine_weights(skill_score)

    # weighted sum combining all signals into a single relevance score
    final_score = (
        weight_semantic * semantic_score +
        weight_skill * skill_score +
        weight_experience * experience_score +
        weight_role * role_score +
        weight_availability * availability_score +
        weight_fairness * workload_score
    )

    # convert continuous scores into readable percentages
    score_percent = max(0, min(100, round(final_score * 100)))
    availability_percent = max(0, min(100, round(availability_score * 100)))
    availability_label = _availability_label(availability_percent)

    # generate explanation text
    reason = _build_reason(
        matched_skills,
        matched_goals,
        role_score,
        employee["role"],
        employee["experience"],
        availability_percent,
        workload_score,
    )

    # final structure to return to frontend / api
    return {
        "employee_id": employee["employee_id"],
        "name": employee["name"],
        "role": employee["role"],
        "score_percent": score_percent,
        "availability_percent": availability_percent,
        "availability_label": availability_label,
        "skills": matched_skills,
        "learning_goals": matched_goals,
        "workload_score": workload_score,
        "reason": reason,
        "final_score": final_score,
    }
