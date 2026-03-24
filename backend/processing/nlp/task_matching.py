from sentence_transformers import SentenceTransformer, util
from ..task_data_access import (
    fetch_employees_by_user,
    calculate_assignment_availability,
    fetch_employee_feedback,
)
from .task_scoring import (
    normalize_experience,
    compute_role_match,
    build_recommendation_entry,
)
from processing.settings_processing import fetch_user_settings

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
def _skill_label_and_weight(raw_skill):
    if isinstance(raw_skill, dict):
        label = str(raw_skill.get("skill_name") or "").strip()
        years = raw_skill.get("years_experience")
        derived = bool(raw_skill.get("derived"))
    else:
        label = str(raw_skill).strip()
        years = None
        derived = False
    if not label:
        return None, 0.0, 0.0, False
    try:
        years_val = float(years) if years is not None else 0.0
    except Exception:
        years_val = 0.0
    weight = 1.0 + max(0.0, min(10.0, years_val))
    return label, years_val, weight, derived


def _skill_candidate_phrases(label: str):
    base = str(label or "").strip().lower()
    if not base:
        return []
    phrases = [
        base,
        f"experience with {base}",
        f"strong {base} skills",
        f"{base} expertise",
        f"knowledge of {base}",
    ]
    # de-duplicate while preserving order
    seen = set()
    unique = []
    for p in phrases:
        if p not in seen:
            unique.append(p)
            seen.add(p)
    return unique


def _score_skills(model, task_description, skills):
    if not skills or not task_description:
        return []

    description = task_description.lower()

    # pre-tokenise description to allow cheap keyword overlap checks
    description_tokens = set(description.replace(",", " ").split())

    # embed the task once because this will be reused for each skill
    task_emb = model.encode(description, convert_to_tensor=True)
    phrase_emb_cache = {}

    scored = []

    for raw_skill in skills:
        label, years_val, weight, derived = _skill_label_and_weight(raw_skill)
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
            best = sim
            for phrase in _skill_candidate_phrases(label):
                skill_emb = phrase_emb_cache.get(phrase)
                if skill_emb is None:
                    skill_emb = model.encode(phrase, convert_to_tensor=True)
                    phrase_emb_cache[phrase] = skill_emb
                best = max(best, util.cos_sim(task_emb, skill_emb).item())
            sim = best

        scored.append({
            "label": label,
            "score": sim,
            "weight": weight,
            "years_experience": years_val,
            "derived": derived,
        })

    return scored


def semantic_skill_match(model, task_description, skills, threshold=0.35):
    scored = _score_skills(model, task_description, skills)
    if not scored:
        return []
    return [m for m in scored if m["score"] >= threshold]


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
    soft_skills = ", ".join(emp.get("soft_skills") or [])
    growth_text = str(emp.get("growth_text") or "").strip()
    soft_clause = f"soft skills: {soft_skills}. " if soft_skills else ""
    if growth_text:
        return (
            f"{emp['role']} with skills: {skills}. "
            f"{soft_clause}"
            f"experience: {emp['experience']} years. "
            f"growth preferences: {growth_text}"
        )
    return f"{emp['role']} with skills: {skills}. {soft_clause}experience: {emp['experience']} years."


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

    settings = fetch_user_settings(user_id)
    custom_weights = settings.get("weights") or {}
    use_custom_weights = bool(settings.get("use_custom_weights"))

    # compute relevant matched-skill experience per employee.
    # use the strongest matched skill instead of adding or averaging years
    # across separate skills, which can imply more total experience than is real.
    def _relevant_experience(scored, matched_labels):
        labels = {str(l).lower() for l in matched_labels}
        years = []
        for item in scored:
            if item.get("derived"):
                continue
            label = str(item.get("label") or "").lower()
            if not label or label not in labels:
                continue
            years_val = item.get("years_experience")
            try:
                if years_val is not None and years_val != "":
                    years.append(float(years_val))
            except Exception:
                continue
        if not years:
            return 0.0
        return max(years)

    skill_scored_cache = []
    relevant_exp_cache = []
    for emp in employees:
        scored = _score_skills(
            model,
            task_description,
            emp.get("skills_detail") or emp["skills"],
        )
        skill_matches = [m for m in scored if m["score"] >= 0.25]
        inferred_labels = [m for m in scored if 0.18 <= m["score"] < 0.25]
        matched_labels = [m["label"] for m in skill_matches] + [m["label"] for m in inferred_labels]
        display_matched_labels = [m["label"] for m in skill_matches if not m.get("derived")] + [
            m["label"] for m in inferred_labels if not m.get("derived")
        ]
        relevant_exp_cache.append(_relevant_experience(scored, matched_labels))
        skill_scored_cache.append(scored)

    max_exp = max(relevant_exp_cache, default=1) or 1
    max_workload = max((e.get("recent_workload_hours", 0) for e in employees), default=0)

    # embed task and employees once
    task_emb = encode_task(model, task_description)
    emp_embs = encode_employees(model, employees)

    # compute similarity between task and all employees in one batch
    sims = util.cos_sim(task_emb, emp_embs)[0]

    ranked = []

    # evaluate each employee individually
    feedback_cache = {}
    task_phrase_cache = {}

    def _feedback_score(task_emb, feedback_items):
        if not feedback_items:
            return 0.0
        rating_weight = {
            "Excellent": 1.0,
            "Good": 0.7,
            "Average": 0.4,
            "Poor": 0.0,
        }
        scored = []
        for item in feedback_items:
            desc = str(item.get("task_description") or "").strip()
            rating = str(item.get("performance_rating") or "").strip()
            notes = str(item.get("feedback_notes") or "").strip()
            if rating not in rating_weight:
                continue

            similarity_parts = []

            if desc:
                desc_emb = task_phrase_cache.get(desc)
                if desc_emb is None:
                    desc_emb = model.encode(desc, convert_to_tensor=True)
                    task_phrase_cache[desc] = desc_emb
                similarity_parts.append(float(util.cos_sim(task_emb, desc_emb).item()))

            if notes:
                # Manager notes often capture nuanced strengths/weaknesses that
                # the original task title misses, so fold them into similarity.
                notes_emb = task_phrase_cache.get(notes)
                if notes_emb is None:
                    notes_emb = model.encode(notes, convert_to_tensor=True)
                    task_phrase_cache[notes] = notes_emb
                similarity_parts.append(float(util.cos_sim(task_emb, notes_emb).item()))

            if not similarity_parts:
                continue

            sim = sum(similarity_parts) / len(similarity_parts)
            scored.append(sim * rating_weight[rating])
        if not scored:
            return 0.0
        top = sorted(scored, reverse=True)[:3]
        return max(0.0, min(1.0, sum(top) / len(top)))

    for idx, emp in enumerate(employees):

        # semantic similarity between task and employee profile
        semantic = float(sims[idx])

        # normalise relevant experience to a 0-1 scale
        relevant_exp = relevant_exp_cache[idx]
        exp_score = normalize_experience(relevant_exp, max_exp)

        # evaluate whether the employee's role fits the task title/keywords
        role_score = compute_role_match(task_description, emp["role"])

        # full semantic skill-level matching (technical skills)
        skill_scored = skill_scored_cache[idx]
        skill_matches = [m for m in skill_scored if m["score"] >= 0.25]
        inferred_skill = [m for m in skill_scored if 0.18 <= m["score"] < 0.25]
        matched_labels = [m["label"] for m in skill_matches] + [m["label"] for m in inferred_skill]
        display_matched_labels = [m["label"] for m in skill_matches if not m.get("derived")] + [
            m["label"] for m in inferred_skill if not m.get("derived")
        ]
        possible_skill_labels = []
        display_possible_skill_labels = []
        possible_skill_score = 0.0
        possible_skill_candidates = [
            m for m in skill_scored if 0.18 <= m["score"] < 0.25
        ]
        if not matched_labels and possible_skill_candidates:
            possible_skill_labels = [
                m["label"]
                for m in sorted(possible_skill_candidates, key=lambda x: x["score"], reverse=True)
            ][:3]
            display_possible_skill_labels = [
                m["label"]
                for m in sorted(
                    [m for m in possible_skill_candidates if not m.get("derived")],
                    key=lambda x: x["score"],
                    reverse=True,
                )
            ][:3]
        if possible_skill_candidates:
            top_possible = sorted(
                possible_skill_candidates, key=lambda x: x["score"], reverse=True
            )[:3]
            possible_skill_score = sum(m["score"] for m in top_possible) / len(top_possible)

        # role-expanded (derived) skill keywords that align with the task
        expanded_skill_labels = []
        derived_candidates = [
            m for m in skill_scored
            if m.get("derived") and m.get("label") and m["score"] >= 0.18
        ]
        if derived_candidates:
            used = {s.lower() for s in (display_matched_labels + display_possible_skill_labels)}
            top_derived = sorted(derived_candidates, key=lambda x: x["score"], reverse=True)[:5]
            for item in top_derived:
                label = str(item.get("label") or "").strip()
                if not label:
                    continue
                if label.lower() in used:
                    continue
                expanded_skill_labels.append(label)
                if len(expanded_skill_labels) >= 3:
                    break

        # weighted average match score across matched skills (by years experience)
        total_weight = sum(m.get("weight", 1.0) for m in skill_matches)
        avg_skill_sim = (
            sum(m["score"] * m.get("weight", 1.0) for m in skill_matches) / total_weight
            if skill_matches and total_weight > 0 else 0
        )

        # coverage: what percentage of the employee's skills are relevant
        coverage = (
            len(matched_labels) / len(emp["skills"]) if emp["skills"] else 0
        )

        # learning goals are a secondary signal
        raw_goals = emp.get("learning_goals") or []
        clean_goals = [g for g in raw_goals if str(g or "").strip()]
        goal_matches = semantic_skill_match(model, task_description, clean_goals, threshold=0.4)
        goal_score = (
            sum(m["score"] for m in goal_matches) / len(goal_matches)
            if goal_matches else 0
        )
        goal_bonus = min(0.15, goal_score * 0.15)

        # final skill score picks whichever is stronger:
        # semantic similarity vs. skill coverage
        skill_score = min(1.0, max(avg_skill_sim, coverage) + goal_bonus)

        # soft skill matching (boost only)
        soft_scored = _score_skills(
            model,
            task_description,
            emp.get("soft_skills_detail") or emp.get("soft_skills") or [],
        )
        soft_skill_matches = [m for m in soft_scored if m["score"] >= 0.25]
        inferred_soft_labels = [
            m["label"]
            for m in soft_scored
            if 0.18 <= m["score"] < 0.25
        ]
        matched_soft_labels = [m["label"] for m in soft_skill_matches] + inferred_soft_labels
        possible_soft_labels = []
        possible_soft_score = 0.0
        possible_soft_candidates = [
            m for m in soft_scored if 0.18 <= m["score"] < 0.25
        ]
        if not matched_soft_labels and possible_soft_candidates:
            possible_soft_labels = [
                m["label"]
                for m in sorted(possible_soft_candidates, key=lambda x: x["score"], reverse=True)
            ][:3]
        if possible_soft_candidates:
            top_possible_soft = sorted(
                possible_soft_candidates, key=lambda x: x["score"], reverse=True
            )[:3]
            possible_soft_score = sum(m["score"] for m in top_possible_soft) / len(top_possible_soft)
        soft_weight = sum(m.get("weight", 1.0) for m in soft_skill_matches)
        soft_skill_score = (
            sum(m["score"] * m.get("weight", 1.0) for m in soft_skill_matches) / soft_weight
            if soft_skill_matches and soft_weight > 0 else 0
        )

        # preferences + learning goals free-text score
        preferences_score = 0.0
        growth_text = str(emp.get("growth_text") or "").strip()
        preferences_present = bool(growth_text)
        if growth_text:
            pref_emb = model.encode(growth_text, convert_to_tensor=True)
            preferences_score = float(util.cos_sim(task_emb, pref_emb).item())

        # feedback score: past ratings on similar tasks
        emp_feedback = feedback_cache.get(emp["employee_id"])
        if emp_feedback is None:
            emp_feedback = fetch_employee_feedback(user_id, emp["employee_id"])
            feedback_cache[emp["employee_id"]] = emp_feedback
        feedback_score = _feedback_score(task_emb, emp_feedback)

        # availability score ranges from 0 (fully unavailable) to 1 (fully available)
        availability = calculate_assignment_availability(
            emp["employee_id"], start_date, end_date
        )

        # fairness score: lighter recent workloads get a small boost
        recent_workload = float(emp.get("recent_workload_hours", 0) or 0)
        if max_workload > 0:
            workload_score = max(0.0, 1 - (recent_workload / max_workload))
        else:
            workload_score = 1.0

        # combine all computed scores into a single result entry
        emp_for_reason = {**emp, "experience": relevant_exp}
        ranked.append(
            build_recommendation_entry(
                emp_for_reason,
                semantic,
                skill_score,
                soft_skill_score,
                exp_score,
                role_score,
                availability,
                feedback_score,
                preferences_present,
                display_matched_labels,
                matched_soft_labels,
                display_possible_skill_labels or possible_skill_labels,
                possible_soft_labels,
                expanded_skill_labels,
                possible_skill_score,
                possible_soft_score,
                [m["label"] for m in goal_matches],
                workload_score,
                preferences_score,
                custom_weights,
                use_custom_weights,
            )
        )

    # final sorting: highest score first
    return sorted(ranked, key=lambda x: x["final_score"], reverse=True)
