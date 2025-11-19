from datetime import datetime
from processing.nlp.task_matching import score_employee
from processing.availability_processing import calculate_availability
import json
from db import get_connection


def compute_recommendations(task_description: str, start_date: str, end_date: str):
    conn = get_connection()
    cur = conn.cursor()

    # Fetch employees from latest upload
    cur.execute("""
        SELECT employee_id, name, role, experience_years, skills
        FROM employees
        WHERE upload_id = (
            SELECT upload_id FROM uploads
            WHERE is_active = TRUE
            ORDER BY upload_date DESC
            LIMIT 1
        );
    """)

    rows = cur.fetchall()
    results = []

    d_start = datetime.strptime(start_date, "%Y-%m-%d").date()
    d_end = datetime.strptime(end_date, "%Y-%m-%d").date()

    for emp_id, name, role, exp_years, skills_raw in rows:

        # ---- Parse Skills ----
        if isinstance(skills_raw, str):
            try:
                skills = json.loads(skills_raw)
            except:
                skills = []
        else:
            skills = skills_raw or []

        skills = [str(s).lower().strip() for s in skills]

        # ---- 1. NLP SIMILARITY ----
        # score_employee returns: (similarity_score, matched_skills)
        nlp_score, matched_skills = score_employee(task_description, skills)

        # ---- 2. PURE SKILL MATCH SCORE (dominant factor) ----
        # 0 matched skills -> 0.  
        # 5+ matched skills -> capped at 1.0
        skill_score = min(len(matched_skills) / 5, 1.0)

        # ---- 3. EXPERIENCE SCORE ----
        exp_score = min(float(exp_years or 0) / 10, 1.0)

        # ---- 4. AVAILABILITY SCORE ----
        availability = calculate_availability(emp_id, d_start, d_end)
        status = availability["status"]

        if status == "Available":
            avail_score = 1.0
        elif status == "Partial":
            pct = availability["percent"]
            avail_score = max(0.4, min(0.8, pct / 100))
        else:
            avail_score = 0.2  # Busy is heavily penalized

        # ---- FINAL WEIGHTED SCORE ----
        # Skills dominate, NLP supports, experience + availability adjust
        final = (
            0.50 * skill_score +
            0.30 * nlp_score +
            0.15 * exp_score +
            0.05 * avail_score
        )

        reason = (
            f"{name} matches {len(matched_skills)} required skills, "
            f"has {exp_years} years experience, "
            f"and is {availability['status']} during this period."
        )

        results.append({
            "employee_id": emp_id,
            "name": name,
            "role": role,
            "score": round(final, 3),
            "matched_skills": matched_skills,
            "availability": availability,
            "reason": reason
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
