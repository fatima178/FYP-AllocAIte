from datetime import datetime, timedelta
import re
from typing import Dict, List, Sequence, Set

from dateutil import parser

from db import get_connection
from processing.recommendations.recommend_processing import (
    RecommendationError,
    generate_recommendations,
)

try:
    from sentence_transformers import SentenceTransformer, util
except Exception:  # pragma: no cover - optional dependency at runtime
    SentenceTransformer = None
    util = None


INTENT_EXAMPLES: Dict[str, Sequence[str]] = {
    "availability": (
        "who is available next week",
        "who is free tomorrow",
        "show me employees who are busy this week",
        "who can take on work on friday",
    ),
    "assignment": (
        "what is someone working on this week",
        "what task is an employee assigned to",
        "who is working on onboarding",
        "what is a team member working on next week",
    ),
    "skills": (
        "who has python skills",
        "show employees with sql and api experience",
        "who knows frontend development",
        "find people with ux skills",
    ),
    "role": (
        "show all backend developers",
        "list the designers",
        "who are the analysts",
        "show frontend engineers",
    ),
    "employee_summary": (
        "tell me about an employee",
        "show employee profile",
        "what do you know about this team member",
        "summarise this employee",
    ),
    "hiring": (
        "who should i hire for a specific task",
        "do we need to hire for this task",
        "who is the best fit for this task",
        "recommend someone for this project",
    ),
}

INTENT_KEYWORDS: Dict[str, Sequence[str]] = {
    "availability": ("available", "availability", "free", "busy", "capacity"),
    "assignment": ("doing", "working", "assigned", "assignment", "task", "project"),
    "skills": ("skill", "skills", "know", "knows", "expert", "experience", "tech stack"),
    "role": ("role", "roles", "developer", "engineer", "designer", "analyst", "backend", "frontend"),
    "employee_summary": ("about", "profile", "summary", "summarise", "details"),
    "hiring": ("hire", "hiring", "recruit", "recommend", "best fit", "staff", "candidate"),
}

SKILL_ALIASES: Dict[str, Sequence[str]] = {
    "python": ("python", "py"),
    "sql": ("sql", "postgres", "postgresql", "database", "databases"),
    "api": ("api", "apis", "rest", "backend api"),
    "backend": ("backend", "server side", "server-side"),
    "frontend": ("frontend", "front end", "front-end", "ui"),
    "ux": ("ux", "user experience"),
    "design": ("design", "designer", "figma", "product design"),
    "nlp": ("nlp", "natural language processing"),
    "tensorflow": ("tensorflow", "tf"),
    "django": ("django",),
}

ROLE_ALIASES: Dict[str, Sequence[str]] = {
    "backend": ("backend", "backend developer", "backend engineer", "api developer"),
    "frontend": ("frontend", "frontend developer", "frontend engineer", "ui engineer"),
    "developer": ("developer", "engineer", "software engineer"),
    "designer": ("designer", "design", "ux designer", "ui designer"),
    "analyst": ("analyst", "analysis", "data analyst", "business analyst"),
    "manager": ("manager", "lead", "team lead"),
}

_EMBEDDING_MODEL = None
_INTENT_EMBEDDINGS = None


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def tokenize(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9]+", normalize_text(text)))


def format_date_range_label(start, end) -> str:
    if start == end:
        return start.isoformat()
    return f"{start.isoformat()} to {end.isoformat()}"


def parse_date_range(text: str):
    t = normalize_text(text)
    now = datetime.today()

    if "today" in t:
        return now.date(), now.date()

    if "tomorrow" in t:
        d = now + timedelta(days=1)
        return d.date(), d.date()

    if "yesterday" in t:
        d = now - timedelta(days=1)
        return d.date(), d.date()

    match = re.search(r"in (\d+) days", t)
    if match:
        offset = int(match.group(1))
        d = now + timedelta(days=offset)
        return d.date(), d.date()

    match = re.search(r"next (\d+) weeks?", t)
    if match:
        weeks = max(1, int(match.group(1)))
        start = now + timedelta(days=(7 - now.weekday()))
        end = start + timedelta(days=weeks * 7 - 1)
        return start.date(), end.date()

    if "next week" in t:
        start = now + timedelta(days=(7 - now.weekday()))
        end = start + timedelta(days=6)
        return start.date(), end.date()

    if "this week" in t:
        start = now - timedelta(days=now.weekday())
        end = start + timedelta(days=6)
        return start.date(), end.date()

    if "this month" in t:
        start = now.replace(day=1)
        next_month = (start + timedelta(days=32)).replace(day=1)
        end = next_month - timedelta(days=1)
        return start.date(), end.date()

    if "next month" in t:
        start = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
        end = ((start + timedelta(days=32)).replace(day=1) - timedelta(days=1))
        return start.date(), end.date()

    between_match = re.search(r"(?:between|from)\s+(.+?)\s+(?:and|to)\s+(.+)", t)
    if between_match:
        start_text, end_text = between_match.groups()
        try:
            start = parser.parse(start_text, fuzzy=True).date()
            end = parser.parse(end_text, fuzzy=True).date()
            return (start, end) if start <= end else (end, start)
        except Exception:
            pass

    iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", t)
    if iso_dates:
        try:
            start = parser.parse(iso_dates[0]).date()
            end = parser.parse(iso_dates[-1]).date()
            return (start, end) if start <= end else (end, start)
        except Exception:
            pass

    try:
        d = parser.parse(t, fuzzy=True, default=now).date()
        return d, d
    except Exception:
        return None, None


def get_semantic_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL
    if SentenceTransformer is None:
        return None
    try:
        _EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        _EMBEDDING_MODEL = None
    return _EMBEDDING_MODEL


def get_intent_embeddings():
    global _INTENT_EMBEDDINGS
    if _INTENT_EMBEDDINGS is not None:
        return _INTENT_EMBEDDINGS
    model = get_semantic_model()
    if model is None:
        return None
    texts = [example for examples in INTENT_EXAMPLES.values() for example in examples]
    try:
        _INTENT_EMBEDDINGS = model.encode(texts, convert_to_tensor=True)
    except Exception:
        _INTENT_EMBEDDINGS = None
    return _INTENT_EMBEDDINGS


def semantic_intent_scores(message: str) -> Dict[str, float]:
    model = get_semantic_model()
    intent_embeddings = get_intent_embeddings()
    if model is None or intent_embeddings is None or util is None:
        return {}

    try:
        query_embedding = model.encode(message, convert_to_tensor=True)
        similarities = util.cos_sim(query_embedding, intent_embeddings)[0].tolist()
    except Exception:
        return {}

    scores: Dict[str, float] = {}
    offset = 0
    for intent, examples in INTENT_EXAMPLES.items():
        slice_scores = similarities[offset : offset + len(examples)]
        offset += len(examples)
        scores[intent] = max(slice_scores) if slice_scores else 0.0
    return scores


def lexical_intent_scores(message: str) -> Dict[str, float]:
    normalized = normalize_text(message)
    message_tokens = tokenize(normalized)
    scores: Dict[str, float] = {}

    for intent, keywords in INTENT_KEYWORDS.items():
        keyword_score = sum(1 for keyword in keywords if keyword in normalized)
        example_score = 0.0
        for example in INTENT_EXAMPLES[intent]:
            example_tokens = tokenize(example)
            if example_tokens:
                example_score = max(example_score, len(message_tokens & example_tokens) / len(example_tokens))
        scores[intent] = keyword_score + example_score

    return scores


def merge_scores(*score_maps: Dict[str, float]) -> Dict[str, float]:
    merged: Dict[str, float] = {}
    for score_map in score_maps:
        for key, value in score_map.items():
            merged[key] = merged.get(key, 0.0) + value
    return merged


def get_employee_directory(cur, user_id: int) -> List[Dict[str, object]]:
    cur.execute(
        """
        SELECT employee_id, name, COALESCE(role, ''), COALESCE(department, '')
        FROM "Employees"
        WHERE user_id = %s
        ORDER BY name ASC;
        """,
        (user_id,),
    )
    return [
        {
            "employee_id": row[0],
            "name": row[1],
            "role": row[2],
            "department": row[3],
        }
        for row in cur.fetchall()
    ]


def parse_employee(employees: Sequence[Dict[str, object]], text: str):
    normalized = normalize_text(text)
    message_tokens = tokenize(normalized)

    best_match = None
    best_score = 0.0
    for employee in employees:
        name = normalize_text(employee["name"])
        first_name = name.split(" ")[0] if name else ""
        name_tokens = tokenize(name)

        score = 0.0
        if name and name in normalized:
            score = 3.0
        elif first_name and re.search(rf"\b{re.escape(first_name)}\b", normalized):
            score = 2.0
        elif name_tokens:
            overlap = len(message_tokens & name_tokens)
            if overlap:
                score = overlap / len(name_tokens)

        if score > best_score:
            best_match = employee
            best_score = score

    return best_match if best_score >= 1.0 else None


def get_known_skills(cur, user_id: int) -> List[str]:
    cur.execute(
        """
        SELECT DISTINCT lower(skill_name)
        FROM "EmployeeSkills" es
        JOIN "Employees" e ON e.employee_id = es.employee_id
        WHERE e.user_id = %s
        ORDER BY lower(skill_name);
        """,
        (user_id,),
    )
    return [row[0] for row in cur.fetchall() if row[0]]


def get_known_roles(cur, user_id: int) -> List[str]:
    cur.execute(
        """
        SELECT DISTINCT lower(role)
        FROM "Employees"
        WHERE user_id = %s AND role IS NOT NULL AND trim(role) <> ''
        ORDER BY lower(role);
        """,
        (user_id,),
    )
    return [row[0] for row in cur.fetchall() if row[0]]


def expand_alias_hits(text: str, alias_map: Dict[str, Sequence[str]]) -> Set[str]:
    normalized = normalize_text(text)
    hits = set()
    for canonical, aliases in alias_map.items():
        if any(alias in normalized for alias in aliases):
            hits.add(canonical)
    return hits


def parse_skills(cur, user_id: int, text: str) -> List[str]:
    normalized = normalize_text(text)
    hits = expand_alias_hits(normalized, SKILL_ALIASES)
    db_skills = get_known_skills(cur, user_id)

    for skill in db_skills:
        skill_tokens = tokenize(skill)
        if skill in normalized or (skill_tokens and skill_tokens <= tokenize(normalized)):
            hits.add(skill)

    return sorted(hits)


def parse_role_filters(cur, user_id: int, text: str) -> List[str]:
    normalized = normalize_text(text)
    hits = expand_alias_hits(normalized, ROLE_ALIASES)
    db_roles = get_known_roles(cur, user_id)

    for role in db_roles:
        role_tokens = tokenize(role)
        if role in normalized or (role_tokens and role_tokens <= tokenize(normalized)):
            hits.add(role)

    return sorted(hits)


def detect_intent(cur, user_id: int, message: str) -> str:
    lexical_scores = lexical_intent_scores(message)
    semantic_scores = semantic_intent_scores(message)
    scores = merge_scores(lexical_scores, semantic_scores)

    employees = get_employee_directory(cur, user_id)
    employee_match = parse_employee(employees, message)
    skills = parse_skills(cur, user_id, message)
    roles = parse_role_filters(cur, user_id, message)
    start, _ = parse_date_range(message)

    if employee_match:
        scores["assignment"] = scores.get("assignment", 0.0) + 1.25
        scores["employee_summary"] = scores.get("employee_summary", 0.0) + 0.75
    if skills:
        scores["skills"] = scores.get("skills", 0.0) + 1.5
    if roles:
        scores["role"] = scores.get("role", 0.0) + 1.5
    if start:
        scores["availability"] = scores.get("availability", 0.0) + 0.75
        scores["assignment"] = scores.get("assignment", 0.0) + 0.5
    if any(keyword in normalize_text(message) for keyword in INTENT_KEYWORDS["hiring"]):
        scores["hiring"] = scores.get("hiring", 0.0) + 1.75

    best_intent = max(scores, key=scores.get) if scores else "fallback"
    threshold = 0.75 if semantic_scores else 0.6
    return best_intent if scores.get(best_intent, 0.0) >= threshold else "fallback"


def handle_availability(cur, user_id: int, message: str):
    start, end = parse_date_range(message)
    if not start:
        return {
            "response": (
                "I couldn’t understand the timeframe. Try 'next week', 'tomorrow', "
                "or a range like 'from 2026-04-01 to 2026-04-05'."
            )
        }

    cur.execute(
        """
        SELECT e.name
        FROM "Employees" e
        WHERE e.user_id = %s
          AND e.employee_id NOT IN (
              SELECT a.employee_id
              FROM "Assignments" a
              JOIN "Employees" ea ON ea.employee_id = a.employee_id
              WHERE ea.user_id = %s
                AND a.employee_id IS NOT NULL
                AND a.start_date <= %s
                AND a.end_date >= %s
          )
        ORDER BY e.name ASC;
        """,
        (user_id, user_id, end, start),
    )
    names = [row[0] for row in cur.fetchall()]

    if not names:
        return {"response": f"No one is available between {format_date_range_label(start, end)}."}

    preview = ", ".join(names[:10])
    suffix = "" if len(names) <= 10 else f" and {len(names) - 10} more"
    return {
        "response": (
            f"Available between {format_date_range_label(start, end)}: {preview}{suffix}."
        )
    }


def handle_skills(cur, user_id: int, message: str):
    skills = parse_skills(cur, user_id, message)
    if not skills:
        known_skills = get_known_skills(cur, user_id)[:8]
        suggestion_text = ", ".join(known_skills) if known_skills else "python, sql, frontend"
        return {"response": f"Specify a skill to search for, for example: {suggestion_text}."}

    conditions = []
    params: List[object] = [user_id]
    for skill in skills:
        conditions.append("lower(es.skill_name) LIKE %s")
        params.append(f"%{skill}%")

    where_clause = " OR ".join(conditions)
    cur.execute(
        f"""
        SELECT DISTINCT e.name
        FROM "Employees" e
        JOIN "EmployeeSkills" es ON e.employee_id = es.employee_id
        WHERE e.user_id = %s
          AND ({where_clause})
        ORDER BY e.name ASC;
        """,
        params,
    )

    names = [row[0] for row in cur.fetchall()]
    if not names:
        return {"response": f"No employees found with skills matching: {', '.join(skills)}."}

    return {"response": f"Employees with {', '.join(skills)}: {', '.join(names)}."}


def handle_assignment(cur, user_id: int, message: str):
    employees = get_employee_directory(cur, user_id)
    employee = parse_employee(employees, message)
    if not employee:
        return {"response": "I couldn’t find that employee. Try a first name or full name."}

    start, end = parse_date_range(message)
    if not start:
        start = datetime.today().date()
        end = start

    cur.execute(
        """
        SELECT title, start_date, end_date
        FROM "Assignments"
        WHERE employee_id = %s
          AND start_date <= %s
          AND end_date >= %s
        ORDER BY start_date ASC, title ASC;
        """,
        (employee["employee_id"], end, start),
    )
    tasks = cur.fetchall()

    if not tasks:
        return {
            "response": (
                f"{employee['name']} has no assignments between {format_date_range_label(start, end)}."
            )
        }

    formatted = ", ".join(
        f"{title} ({task_start.isoformat()} to {task_end.isoformat()})"
        for title, task_start, task_end in tasks
    )
    return {
        "response": (
            f"{employee['name']} is scheduled for {formatted} "
            f"during {format_date_range_label(start, end)}."
        )
    }


def handle_role(cur, user_id: int, message: str):
    roles = parse_role_filters(cur, user_id, message)
    if not roles:
        known_roles = get_known_roles(cur, user_id)[:8]
        if not known_roles:
            return {"response": "I couldn’t find any role data for this team yet."}
        return {"response": f"Try a role like: {', '.join(known_roles)}."}

    conditions = []
    params: List[object] = [user_id]
    for role in roles:
        conditions.append("lower(role) LIKE %s")
        params.append(f"%{role}%")

    cur.execute(
        f"""
        SELECT name, role
        FROM "Employees"
        WHERE user_id = %s
          AND ({' OR '.join(conditions)})
        ORDER BY name ASC;
        """,
        params,
    )
    rows = cur.fetchall()

    if not rows:
        return {"response": f"No employees found for roles matching: {', '.join(roles)}."}

    formatted = ", ".join(f"{name} ({role})" for name, role in rows[:12])
    suffix = "" if len(rows) <= 12 else f" and {len(rows) - 12} more"
    return {"response": f"Employees matching {', '.join(roles)}: {formatted}{suffix}."}


def handle_employee_summary(cur, user_id: int, message: str):
    employees = get_employee_directory(cur, user_id)
    employee = parse_employee(employees, message)
    if not employee:
        return {"response": "I couldn’t find that employee. Try a first name or full name."}

    cur.execute(
        """
        SELECT skill_name
        FROM "EmployeeSkills"
        WHERE employee_id = %s
        ORDER BY years_experience DESC NULLS LAST, skill_name ASC
        LIMIT 6;
        """,
        (employee["employee_id"],),
    )
    skills = [row[0] for row in cur.fetchall()]

    today = datetime.today().date()
    cur.execute(
        """
        SELECT title
        FROM "Assignments"
        WHERE employee_id = %s
          AND start_date <= %s
          AND end_date >= %s
        ORDER BY start_date ASC, title ASC
        LIMIT 5;
        """,
        (employee["employee_id"], today, today),
    )
    active_tasks = [row[0] for row in cur.fetchall()]

    parts = [f"{employee['name']} is a {employee['role'] or 'team member'}"]
    if employee["department"]:
        parts[-1] += f" in {employee['department']}"
    if skills:
        parts.append(f"Top skills: {', '.join(skills)}")
    if active_tasks:
        parts.append(f"Current work: {', '.join(active_tasks)}")

    return {"response": ". ".join(parts) + "."}


def build_hiring_task_description(message: str) -> str:
    normalized = re.sub(
        r"\b(who should i hire|who can i hire|do we need to hire|recommend someone|best fit|for this task|for this project|for this role)\b",
        " ",
        normalize_text(message),
    )
    normalized = re.sub(r"\s+", " ", normalized).strip(" ?.")
    return normalized or message.strip()


def handle_hiring(cur, user_id: int, message: str):
    start, end = parse_date_range(message)
    if not start:
        start = datetime.today().date()
        end = start + timedelta(days=6)

    task_description = build_hiring_task_description(message)

    try:
        result = generate_recommendations(
            task_description=task_description,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            user_id=user_id,
            upload_id=None,
        )
    except RecommendationError as exc:
        return {"response": exc.message}

    recommendations = result.get("recommendations") or []
    gap_analysis = result.get("gap_analysis")

    if recommendations:
        top_matches = recommendations[:3]
        match_text = "; ".join(
            f"{rec.get('name')} ({rec.get('score_percent')}%)"
            for rec in top_matches
            if rec.get("name")
        )
        response_parts = [
            f"For '{task_description}' during {format_date_range_label(start, end)}, top internal matches are: {match_text}."
        ]
    else:
        response_parts = [
            f"I could not find a strong internal match for '{task_description}' during {format_date_range_label(start, end)}."
        ]

    if gap_analysis:
        gap_message = gap_analysis.get("message")
        missing_skills = gap_analysis.get("missing_skills") or []
        suggested_roles = gap_analysis.get("suggested_roles") or []
        if gap_message:
            response_parts.append(gap_message)
        if missing_skills:
            response_parts.append(f"Missing skills: {', '.join(missing_skills)}.")
        if suggested_roles:
            response_parts.append(f"Suggested hiring roles: {', '.join(suggested_roles)}.")

    return {"response": " ".join(response_parts)}


def build_fallback_examples(cur, user_id: int) -> List[str]:
    skills = get_known_skills(cur, user_id)
    roles = get_known_roles(cur, user_id)
    employees = get_employee_directory(cur, user_id)

    examples = ["Who is available next week?"]
    examples.append(
        f"Who has {skills[0]} skills?" if skills else "Who has Python skills?"
    )
    examples.append(
        f"Show employees with {roles[0]} roles"
        if roles
        else "Show employees with backend roles"
    )
    examples.append(
        f"What is {employees[0]['name']} working on this week?"
        if employees
        else "What is someone working on this week?"
    )
    examples.append("Who should I hire for a backend API task?")
    return examples


def handle_fallback(cur, user_id: int):
    examples = build_fallback_examples(cur, user_id)
    return {
        "response": "I can help with availability, assignments, skills, roles, and employee summaries. "
        + "Try one of these: "
        + " | ".join(examples)
    }


def get_chatbot_suggestions(user_id: int) -> List[str]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT 1 FROM "Employees" WHERE user_id = %s LIMIT 1;', (user_id,))
        if not cur.fetchone():
            return build_fallback_examples(cur, user_id)
        return build_fallback_examples(cur, user_id)
    finally:
        cur.close()
        conn.close()


def log_chat(cur, user_id: int, message: str, response: str):
    try:
        cur.execute(
            """
            INSERT INTO "ChatLogs" (user_id, query_text, response_text)
            VALUES (%s, %s, %s);
            """,
            (user_id, message, response),
        )
    except Exception:
        pass


def handle_chatbot_query(message: str, user_id: int):
    message = (message or "").strip()
    if not message:
        raise ValueError("missing message")
    if not user_id:
        raise ValueError("missing user_id")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT 1 FROM "Employees" WHERE user_id = %s LIMIT 1;', (user_id,))
        if not cur.fetchone():
            return {"response": "No employee data found. Please upload your team sheet first."}

        intent = detect_intent(cur, user_id, message)
        handlers = {
            "availability": handle_availability,
            "skills": handle_skills,
            "assignment": handle_assignment,
            "role": handle_role,
            "employee_summary": handle_employee_summary,
            "hiring": handle_hiring,
            "fallback": lambda cursor, uid, _: handle_fallback(cursor, uid),
        }

        result = handlers.get(intent, handlers["fallback"])(cur, user_id, message)
        log_chat(cur, user_id, message, result.get("response", ""))
        conn.commit()
        return result
    finally:
        cur.close()
        conn.close()
