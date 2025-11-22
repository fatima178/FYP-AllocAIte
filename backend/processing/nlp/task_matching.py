from sentence_transformers import SentenceTransformer, util
import json
from db import get_connection
from .task_scoring import (
    normalize_experience,
    compute_role_match,
    build_recommendation_entry,
)

# Load SBERT model once
model = SentenceTransformer("all-MiniLM-L6-v2")


# ----------------------------------------------------------
# Load employees cleanly from DB
# ----------------------------------------------------------
def fetch_employees(upload_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT employee_id, name, role, experience_years, skills
        FROM Employees
        WHERE upload_id = %s
    """, (upload_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    employees = []
    for r in rows:
        raw_skills = r[4]

        if isinstance(raw_skills, bytes):
            raw_skills = raw_skills.decode("utf-8")

        if isinstance(raw_skills, str):
            try:
                skills = json.loads(raw_skills)
            except json.JSONDecodeError:
                skills = []
        elif isinstance(raw_skills, (list, tuple)):
            skills = list(raw_skills)
        else:
            skills = []

        employees.append({
            "employee_id": r[0],
            "name": r[1],
            "role": r[2],
            "experience": r[3] if r[3] else 0,
            "skills": skills
        })

    return employees


# ----------------------------------------------------------
# SEMANTIC + KEYWORD SKILL MATCHING
# ----------------------------------------------------------
def semantic_skill_match(task_description, skills, threshold=0.45):
    """
    Returns a list of dicts that describe which skills are relevant
    to the task, along with a similarity score. Uses a mix of direct
    keyword matching and SBERT similarity so that “API integration”
    can match “build backend services”, etc.
    """
    if not skills or not task_description:
        return []

    description = task_description.lower()
    description_tokens = set(description.replace(",", " ").split())
    task_emb = model.encode(description, convert_to_tensor=True)

    matches = []
    for raw_skill in skills:
        label = str(raw_skill).strip()
        if not label:
            continue

        normalized = label.lower()
        similarity = 0.0

        if normalized in description:
            similarity = 1.0
        else:
            for token in normalized.replace("/", " ").split():
                if token and token in description_tokens:
                    similarity = 0.75
                    break

        if similarity < 0.75:
            skill_emb = model.encode(normalized, convert_to_tensor=True)
            similarity = max(similarity, util.cos_sim(task_emb, skill_emb).item())

        if similarity >= threshold:
            matches.append({"label": label, "score": similarity})

    return matches


# ----------------------------------------------------------
# Availability from Assignments table
# ----------------------------------------------------------
def calculate_availability(employee_id, start, end):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT remaining_hours, total_hours
        FROM Assignments
        WHERE employee_id = %s
          AND start_date <= %s
          AND end_date >= %s
    """, (employee_id, end, start))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return 1.0

    remaining = sum([r[0] for r in rows if r[0] is not None])
    total = sum([r[1] for r in rows if r[1] is not None])

    if total == 0:
        return 1.0

    return max(0.0, min(1.0, remaining / total))


# ----------------------------------------------------------
# SBERT encoders for employees + task
# ----------------------------------------------------------
def build_employee_text(emp):
    skills = ", ".join(emp["skills"])
    return f"{emp['role']} with skills: {skills}. Experience: {emp['experience']} years."


def encode_task(desc):
    return model.encode(desc, convert_to_tensor=True)


def encode_employees(emps):
    texts = [build_employee_text(e) for e in emps]
    return model.encode(texts, convert_to_tensor=True)


# ----------------------------------------------------------
# MAIN MATCHING ENGINE (with your weights)
# ----------------------------------------------------------
def match_employees(task_description, upload_id, start_date, end_date):
    employees = fetch_employees(upload_id)
    if not employees:
        return []

    max_experience = max((emp["experience"] for emp in employees), default=0) or 1

    task_emb = encode_task(task_description)
    emp_embs = encode_employees(employees)
    sims = util.cos_sim(task_emb, emp_embs)[0]

    ranked = []

    for idx, emp in enumerate(employees):

        semantic = float(sims[idx])  # SBERT embedding similarity
        exp_score = normalize_experience(emp["experience"], max_experience)
        role_score = compute_role_match(task_description, emp["role"])

        matched_skill_data = semantic_skill_match(task_description, emp["skills"])
        matched_skills = [item["label"] for item in matched_skill_data]
        avg_skill_similarity = (
            sum(item["score"] for item in matched_skill_data) / len(matched_skill_data)
            if matched_skill_data
            else 0
        )
        skill_coverage = (
            len(matched_skills) / len(emp["skills"]) if emp["skills"] else 0
        )
        skill_score = max(avg_skill_similarity, skill_coverage)

        availability = calculate_availability(
            emp["employee_id"], start_date, end_date
        )

        ranked.append(
            build_recommendation_entry(
                emp,
                semantic,
                skill_score,
                exp_score,
                role_score,
                availability,
                matched_skills,
            )
        )

    return sorted(ranked, key=lambda x: x["final_score"], reverse=True)
