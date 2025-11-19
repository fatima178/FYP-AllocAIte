from datetime import datetime
from processing.nlp.task_matching import score_employee
from processing.availability_processing import calculate_availability
import json
from db import get_connection

def compute_recommendations(task_description: str, start_date: str, end_date: str):
    conn = get_connection()
    cur = conn.cursor()

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

        # Decode JSON skill list
        if isinstance(skills_raw, str):
            try:
                skills = json.loads(skills_raw)
            except:
                skills = []
        else:
            skills = skills_raw or []

        skills = [str(s).lower().strip() for s in skills]

        # ---- 1. Skill / NLP scoring ----
        # score_employee returns (similarity_score, matched_skills)
        nlp_score, matched_skills = score_employee(task_description, skills)

        # ---- 2. Experience score ----
        # cap at 10 years max
        exp_score = min(float(exp_years or 0) / 10, 1.0)

        # ---- 3. Availability score ----
        availability = calculate_availability(emp_id, d_start, d_end)

        status = availability["status"]

        if status == "Available":
            avail_score = 1.0
        elif status == "Partial":
            # scale based on % availability
            pct = availability["percent"]
            # 0.4 to 0.8 depending on how free they are
            avail_score = max(0.4, min(0.8, pct / 100))
        else:
            # Busy gets punished heavily
            avail_score = 0.2

        # ---- FINAL WEIGHTED SCORE ----
        # 60% skills, 25% experience, 15% availability
        final = (
            0.60 * nlp_score +
            0.25 * exp_score +
            0.15 * avail_score
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
