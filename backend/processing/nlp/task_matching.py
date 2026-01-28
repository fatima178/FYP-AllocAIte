from sentence_transformers import SentenceTransformer, util
from ..task_data_access import (
    fetch_employees_by_user,
    calculate_assignment_availability,
)
from .task_scoring import (
    normalize_experience,
    compute_role_match,
    build_recommendation_entry,
)

# cached global reference to avoid repeatedly loading the model
_DEFAULT_MODEL = None


def get_sentence_model():
    # lazy-load the default sentence transformer model so we only load it once.
    global _DEFAULT_MODEL
    if _DEFAULT_MODEL is None:
        # all-minilm-l6-v2 is compact and fast enough for real-time ranking
        _DEFAULT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _DEFAULT_MODEL


# ----------------------------------------------------------
# semantic + keyword skill matching
# ----------------------------------------------------------
# this function checks if the employee's skills relate to the task description.
# it combines three techniques:
#   1) direct text match (strongest)
#   2) keyword overlap (medium strength)
#   3) sbert similarity (fallback if others don't trigger)
# the result is a list of matched skills with similarity scores.
def semantic_skill_match(model, task_description, skills, threshold=0.45):
    if not skills or not task_description:
        return []

    description = task_description.lower()

    # pre-tokenise description to allow cheap keyword overlap checks
    description_tokens = set(description.replace(",", " ").split())

    # embed the task once because this will be reused for each skill
    task_emb = model.encode(description, convert_to_tensor=True)

    matches = []

    for raw_skill in skills:
        label = str(raw_skill).strip()
        if not label:
            continue

        normal = label.lower()
        sim = 0.0

        # strongest match: skill appears directly in the task text
        if normal in description:
            sim = 1.0

        else:
            # medium match: any token inside the skill label appears in the task tokens
            for tok in normal.replace("/", " ").split():
                if tok and tok in description_tokens:
                    sim = 0.75
                    break

        # fallback: compute semantic similarity with sbert
        if sim < 0.75:
            skill_emb = model.encode(normal, convert_to_tensor=True)
            sim = max(sim, util.cos_sim(task_emb, skill_emb).item())

        # keep only useful matches based on threshold
        if sim >= threshold:
            matches.append({"label": label, "score": sim})

    return matches


# ----------------------------------------------------------
# helper to build SBERT embedding text
# ----------------------------------------------------------
# for each employee, build a descriptive text block that sbert can embed.
# this text combines:
#   - their role
#   - their full skills list
#   - their years of experience
def build_employee_text(emp):
    skills = ", ".join(emp["skills"])
    return f"{emp['role']} with skills: {skills}. experience: {emp['experience']} years."


# encode a task description into an sbert embedding
def encode_task(model, desc):
    return model.encode(desc, convert_to_tensor=True)


# encode all employees into embeddings using the descriptive text builder
def encode_employees(model, emps):
    texts = [build_employee_text(e) for e in emps]
    return model.encode(texts, convert_to_tensor=True)


# ----------------------------------------------------------
# main matching pipeline
# ----------------------------------------------------------
# this is the core function that:
#   1) loads employees
#   2) embeds task and employees
#   3) computes semantic similarity (sbert)
#   4) computes skill match score
#   5) computes experience score
#   6) computes role relevance
#   7) calculates availability
#   8) produces a final ranking
def match_employees(task_description, user_id, start_date, end_date, model=None):
    # fetch employees linked to this upload
    employees = fetch_employees_by_user(user_id)
    if not employees:
        # nothing to match against
        return []

    # ensure we have a model instance
    model = model or get_sentence_model()

    # precompute maximum experience to normalise scores to 0-1 scale
    # avoid division by zero by using default 1
    max_exp = max((e["experience"] for e in employees), default=1)

    # embed task and employees once
    task_emb = encode_task(model, task_description)
    emp_embs = encode_employees(model, employees)

    # compute similarity between task and all employees in one batch
    sims = util.cos_sim(task_emb, emp_embs)[0]

    ranked = []

    # evaluate each employee individually
    for idx, emp in enumerate(employees):

        # semantic similarity between task and employee profile
        semantic = float(sims[idx])

        # normalise experience to a 0-1 scale
        exp_score = normalize_experience(emp["experience"], max_exp)

        # evaluate whether the employee's role fits the task title/keywords
        role_score = compute_role_match(task_description, emp["role"])

        # full semantic skill-level matching
        skill_matches = semantic_skill_match(model, task_description, emp["skills"])
        matched_labels = [m["label"] for m in skill_matches]

        # average match score across matched skills
        avg_skill_sim = (
            sum(m["score"] for m in skill_matches) / len(skill_matches)
            if skill_matches else 0
        )

        # coverage: what percentage of the employee's skills are relevant
        coverage = (
            len(matched_labels) / len(emp["skills"]) if emp["skills"] else 0
        )

        # final skill score picks whichever is stronger:
        # semantic similarity vs. skill coverage
        skill_score = max(avg_skill_sim, coverage)

        # availability score ranges from 0 (fully unavailable) to 1 (fully available)
        availability = calculate_assignment_availability(
            emp["employee_id"], start_date, end_date
        )

        # combine all computed scores into a single result entry
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

    # final sorting: highest score first
    return sorted(ranked, key=lambda x: x["final_score"], reverse=True)
