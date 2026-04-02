from typing import Optional

from db import get_connection
from datetime import date

from processing.nlp.task_matching import match_employees
from processing.recommendations.recommendation_log_processing import (
    create_recommendation_task,
    log_recommendations,
)
from processing.tasks.task_data_access import fetch_employees_by_user


SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "react", "vue", "angular",
    "node", "node.js", "express", "django", "flask", "fastapi", "spring",
    "sql", "postgres", "mysql", "mongodb", "redis", "api", "rest", "graphql",
    "frontend", "backend", "full stack", "fullstack", "ui", "ux", "figma",
    "design", "testing", "qa", "automation", "devops", "docker", "kubernetes",
    "terraform", "aws", "azure", "gcp", "data", "analytics", "etl", "bi",
    "machine learning", "ml", "ai", "nlp", "tensorflow", "pytorch",
    "ios", "android", "react native", "swift", "kotlin", "security",
]

ROLE_HINTS = {
    "Frontend developer": {"react", "vue", "angular", "frontend", "ui", "ux", "figma", "design"},
    "Backend developer": {"python", "java", "node", "node.js", "express", "django", "flask", "fastapi", "spring", "backend", "api", "rest", "graphql", "sql", "postgres", "mysql", "mongodb", "redis"},
    "Full-stack developer": {"frontend", "backend", "react", "javascript", "typescript", "node", "api", "sql"},
    "DevOps engineer": {"devops", "docker", "kubernetes", "terraform", "aws", "azure", "gcp"},
    "Data specialist": {"data", "analytics", "etl", "bi", "sql", "python"},
    "ML engineer": {"machine learning", "ml", "ai", "nlp", "tensorflow", "pytorch", "python"},
    "QA engineer": {"testing", "qa", "automation"},
    "Product designer": {"ui", "ux", "figma", "design"},
    "Mobile developer": {"ios", "android", "react native", "swift", "kotlin"},
    "Security engineer": {"security"},
}


def _extract_task_skill_hints(task_description: str):
    text = str(task_description or "").lower()
    found = []
    for skill in sorted(SKILL_KEYWORDS, key=len, reverse=True):
        if skill in text:
            found.append(skill)

    unique = []
    seen = set()
    for skill in found:
        normalized = skill.replace(".js", "").strip()
        if normalized not in seen:
            unique.append(skill)
            seen.add(normalized)
    return unique


def _suggest_hiring_roles(missing_skills):
    if not missing_skills:
        return []

    missing = {str(skill).lower() for skill in missing_skills}
    scored_roles = []
    for role, role_skills in ROLE_HINTS.items():
        overlap = len(missing & role_skills)
        if overlap > 0:
            scored_roles.append((overlap, role))

    scored_roles.sort(key=lambda item: (-item[0], item[1]))
    return [role for _, role in scored_roles[:3]]


def _build_gap_analysis(task_description: str, user_id: int, recommendations):
    employees = fetch_employees_by_user(user_id)
    org_skills = set()
    for employee in employees:
        for skill in employee.get("skills") or []:
            normalized = str(skill or "").strip().lower()
            if normalized:
                org_skills.add(normalized)
        for skill in employee.get("soft_skills") or []:
            normalized = str(skill or "").strip().lower()
            if normalized:
                org_skills.add(normalized)

    task_skills = _extract_task_skill_hints(task_description)
    missing_skills = [
        skill for skill in task_skills
        if skill.replace(".js", "").strip().lower() not in org_skills
    ]

    top_score = 0
    strong_matches = 0
    for rec in recommendations or []:
        score = rec.get("score_percent")
        if isinstance(score, (int, float)):
            top_score = max(top_score, float(score))
            if score >= 60:
                strong_matches += 1

    weak_internal_fit = (
        not recommendations or
        top_score < 55 or
        strong_matches == 0 or
        len(missing_skills) > 0
    )
    if not weak_internal_fit:
        return None

    suggested_roles = _suggest_hiring_roles(missing_skills)
    severity = "high" if not recommendations or top_score < 45 or len(missing_skills) >= 2 else "medium"

    if not recommendations:
        message = "No internal employee was recommended for this task. Consider hiring or contracting for the missing capability."
    elif missing_skills:
        message = "Current internal coverage looks weak for this task. Some required skills are missing from the team."
    else:
        message = "Current recommendations are relatively weak for this task. You may need extra hiring or external support."

    return {
        "severity": severity,
        "message": message,
        "top_score": round(top_score),
        "missing_skills": missing_skills[:5],
        "suggested_roles": suggested_roles,
    }


# ----------------------------------------------------------
# custom exception for recommendation-related problems
# ----------------------------------------------------------
# carries an http like status code + message so the api layer
# can cleanly return structured errors to the frontend.
class RecommendationError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# ----------------------------------------------------------
# resolve which upload_id should be used
# ----------------------------------------------------------
# logic:
#   - if upload_id explicitly provided:
#       - if user_id given - validate ownership
#       - if no user_id - trust the provided id
#   - if no upload_id provided:
#       - pick latest active upload for the user
#       - fallback to the most recent upload if none active
#   - if none exist - return none
def resolve_upload_id(user_id: Optional[int], upload_id: Optional[int]) -> Optional[int]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        # caller explicitly provided an upload id
        if upload_id is not None:
            if user_id is None:
                # no user to validate against - accept directly
                return upload_id

            # check if the upload actually belongs to this user
            cur.execute(
                """
                SELECT upload_id
                FROM "Uploads"
                WHERE upload_id = %s AND user_id = %s;
                """,
                (upload_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                # user tried to access upload that isn't theirs
                raise RecommendationError(404, "upload not found for this user")
            return row[0]

        # no upload id specified, check by user context
        if user_id is None:
            # without user or upload, there's nothing to resolve
            return None

        # try active upload for the user first
        cur.execute(
            """
            SELECT upload_id
            FROM "Uploads"
            WHERE user_id = %s AND is_active = true
            ORDER BY upload_date DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        # fallback: the latest upload regardless of active flag
        cur.execute(
            """
            SELECT upload_id
            FROM "Uploads"
            WHERE user_id = %s
            ORDER BY upload_date DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None

    finally:
        # always close db resources
        cur.close()
        conn.close()


# ----------------------------------------------------------
# generate employee recommendations for a task
# ----------------------------------------------------------
# this:
#   1) resolves correct upload dataset
#   2) validates there's usable data for the given user
#   3) runs the full ranking pipeline from match_employees()
def generate_recommendations(
    task_description: str,
    start_date: str,
    end_date: str,
    user_id: Optional[int],
    upload_id: Optional[int],
    persist_history: bool = True,
):
    if user_id is None:
        raise RecommendationError(400, "user_id is required")

    employees = fetch_employees_by_user(user_id)
    if not employees:
        raise RecommendationError(
            400,
            "Upload your employee data first before generating recommendations.",
        )

    # run the matching engine and return ranking results
    recommendations = match_employees(task_description, user_id, start_date, end_date)
    gap_analysis = _build_gap_analysis(task_description, user_id, recommendations)

    task_id = None
    if persist_history:
        # record the recommendation request + ranked results for evaluation
        try:
            start_dt = date.fromisoformat(str(start_date))
            end_dt = date.fromisoformat(str(end_date))
            task_id = create_recommendation_task(
                user_id,
                task_description,
                start_dt,
                end_dt,
            )
            log_recommendations(task_id, recommendations)
        except Exception:
            # recommendation logging should not block the response
            task_id = None

    return {
        "task_id": task_id,
        "recommendations": recommendations,
        "gap_analysis": gap_analysis,
    }
