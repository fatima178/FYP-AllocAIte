from sentence_transformers import SentenceTransformer, util
import json
from db import get_connection
from .task_scoring import (
    normalize_experience,
    compute_role_match,
    build_recommendation_entry,
)

# load SBERT model once
model = SentenceTransformer("all-MiniLM-L6-v2")


# ----------------------------------------------------------
# get employees + clean skills
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

        # decode skills JSON safely
        if isinstance(raw_skills, bytes):
            raw_skills = raw_skills.decode("utf-8")

        if isinstance(raw_skills, str):
            try:
                skills = json.loads(raw_skills)
            except:
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
# semantic + keyword skill matching
# ----------------------------------------------------------
def semantic_skill_match(task_description, skills, threshold=0.45):
    if not skills or not task_description:
        return []

    description = task_description.lower()
    description_tokens = set(description.replace(",", " ").split())

    # embed task text
    task_emb = model.encode(description, convert_to_tensor=True)

    matches = []

    for raw_skill in skills:
        label = str(raw_skill).strip()
        if not label:
            continue

        normal = label.lower()
        sim = 0.0

        # direct text match
        if normal in description:
            sim = 1.0
        else:
            # keyword overlap
            for tok in normal.replace("/", " ").split():
                if tok and tok in description_tokens:
                    sim = 0.75
                    break

        # SBERT match if needed
        if sim < 0.75:
            skill_emb = model.encode(normal, convert_to_tensor=True)
            sim = max(sim, util.cos_sim(task_emb, skill_emb).item())

        # only keep useful skills
        if sim >= threshold:
            matches.append({"label": label, "score": sim})

    return matches


# ----------------------------------------------------------
# calculate employee availability
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

    # no assignments = fully free
    if not rows:
        return 1.0

    remaining = sum([r[0] for r in rows if r[0] is not None])
    total = sum([r[1] for r in rows if r[1] is not None])

    if total == 0:
        return 1.0

    return max(0.0, min(1.0, remaining / total))


# ----------------------------------------------------------
# helper to build SBERT embedding text
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
# main matching pipeline
# ----------------------------------------------------------
def match_employees(task_description, upload_id, start_date, end_date):
    # get employees
    employees = fetch_employees(upload_id)
    if not employees:
        return []

    # used for experience normalisation
    max_exp = max((e["experience"] for e in employees), default=1)

    # embed task + employees once
    task_emb = encode_task(task_description)
    emp_embs = encode_employees(employees)

    # SBERT similarities
    sims = util.cos_sim(task_emb, emp_embs)[0]

    ranked = []

    for idx, emp in enumerate(employees):

        semantic = float(sims[idx])              # SBERT score
        exp_score = normalize_experience(emp["experience"], max_exp)
        role_score = compute_role_match(task_description, emp["role"])

        # full semantic skill matching
        skill_matches = semantic_skill_match(task_description, emp["skills"])
        matched_labels = [m["label"] for m in skill_matches]

        # average SBERT skill similarity
        avg_skill_sim = (
            sum(m["score"] for m in skill_matches) / len(skill_matches)
            if skill_matches else 0
        )

        # % of skills that matched
        coverage = (
            len(matched_labels) / len(emp["skills"]) if emp["skills"] else 0
        )

        # pick best skill score
        skill_score = max(avg_skill_sim, coverage)

        availability = calculate_availability(
            emp["employee_id"], start_date, end_date
        )

        # build final entry with all scores
        ranked.append(
            build_recommendation_entry(
                emp,
                semantic,
                skill_score,
                exp_score,
                role_score,
                availability,
                matched_labels,
            )
        )

    # sort by final score
    return sorted(ranked, key=lambda x: x["final_score"], reverse=True)
