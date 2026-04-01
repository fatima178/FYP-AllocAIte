"""database access helpers for recommendation related processing."""

from datetime import datetime
from typing import Any, Dict, List

from db import get_connection
from processing.availability_processing import calculate_availability_from_rows


# ----------------------------------------------------------
# fetch skills for a given employee
# ----------------------------------------------------------
# returns list of dicts with per-skill experience
def _fetch_employee_skills(cur, employee_id: int, skill_type: str) -> List[Dict[str, Any]]:
    cur.execute(
        """
        SELECT skill_name, years_experience
        FROM "EmployeeSkills"
        WHERE employee_id = %s AND skill_type = %s
        ORDER BY skill_name ASC;
        """,
        (employee_id, skill_type),
    )
    return [{"skill_name": s, "years_experience": y} for s, y in cur.fetchall()]


# ----------------------------------------------------------
# fetch learning goals for a given employee
# ----------------------------------------------------------
# returns list of dicts with per-skill priority
def _fetch_employee_learning_goals(cur, employee_id: int) -> List[Dict[str, Any]]:
    cur.execute(
        """
        SELECT skill_name, priority
        FROM "EmployeeLearningGoals"
        WHERE employee_id = %s
        ORDER BY priority DESC, skill_name ASC;
        """,
        (employee_id,),
    )
    return [{"skill_name": s, "priority": p} for s, p in cur.fetchall()]


def _fetch_employee_growth_text(cur, employee_id: int) -> str:
    cur.execute(
        """
        SELECT growth_text
        FROM "EmployeePreferences"
        WHERE employee_id = %s;
        """,
        (employee_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return row[0]


def _merge_skills(skills: List[Dict[str, Any]]):
    merged = {}
    for item in skills:
        name = str(item.get("skill_name") or "").strip()
        if not name:
            continue
        key = name.lower()
        years = item.get("years_experience")
        if key not in merged:
            merged[key] = {"skill_name": name, "years_experience": years}
        else:
            existing = merged[key].get("years_experience")
            try:
                merged[key]["years_experience"] = max(existing or 0, years or 0)
            except Exception:
                merged[key]["years_experience"] = existing or years
    return list(merged.values())


def _derive_role_tags(role: str) -> List[str]:
    if not role:
        return []
    r = role.lower()
    tags = set()
    if "backend" in r:
        tags.update([
            "backend", "api", "server", "rest", "microservices",
            "backend development", "service", "services",
            "authentication", "authorization", "jwt", "oauth",
            "database", "sql", "postgres", "mysql",
        ])
    if "front" in r:
        tags.update([
            "frontend", "ui", "web", "frontend development",
            "react", "vue", "angular", "javascript", "typescript",
            "css", "html",
        ])
    if "full stack" in r or "fullstack" in r:
        tags.update([
            "frontend", "backend", "api", "web", "full stack",
            "react", "node", "express",
        ])
    if "data" in r or "analyst" in r:
        tags.update([
            "data", "analytics", "sql", "etl", "bi",
            "dashboard", "reporting", "metrics", "warehouse",
            "data modeling", "visualization",
        ])
    if "ml" in r or "machine learning" in r:
        tags.update([
            "machine learning", "ml", "ai", "modeling",
            "training", "inference", "classification", "regression",
            "nlp", "computer vision",
        ])
    if "devops" in r:
        tags.update([
            "devops", "infrastructure", "ci/cd", "docker", "kubernetes",
            "terraform", "ansible", "monitoring", "logging",
            "deployment", "pipelines",
        ])
    if "qa" in r or "test" in r:
        tags.update([
            "qa", "testing", "automation",
            "unit testing", "integration testing", "e2e",
            "test cases", "quality assurance",
        ])
    if "design" in r or "ux" in r:
        tags.update([
            "design", "ux", "ui", "figma",
            "wireframes", "prototyping", "user research",
        ])
    if "mobile" in r:
        tags.update([
            "mobile", "ios", "android", "react native",
            "swift", "kotlin",
        ])
    if "security" in r:
        tags.update([
            "security", "infosec", "vulnerability", "threat",
            "risk", "compliance",
        ])
    if "cloud" in r:
        tags.update([
            "cloud", "aws", "azure", "gcp",
            "cloud infrastructure", "serverless",
        ])
    return sorted(tags)


def _fetch_recent_workload_hours(cur, employee_id: int, window_days: int = 90) -> float:
    cur.execute(
        """
        SELECT COALESCE(SUM(COALESCE(total_hours, 0)), 0)
        FROM "Assignments"
        WHERE employee_id = %s
          AND end_date >= CURRENT_DATE - %s;
        """,
        (employee_id, window_days),
    )
    active_total = cur.fetchone()[0] or 0

    cur.execute(
        """
        SELECT COALESCE(SUM(COALESCE(total_hours, 0)), 0)
        FROM "AssignmentHistory"
        WHERE employee_id = %s
          AND end_date >= CURRENT_DATE - %s;
        """,
        (employee_id, window_days),
    )
    history_total = cur.fetchone()[0] or 0
    return float(active_total) + float(history_total)


# ----------------------------------------------------------
# fetch employees for a given upload
# ----------------------------------------------------------
# returns a list of dicts containing:
#   - employee_id
#   - name
#   - role
#   - experience years (defaults to 0 if null)
#   - parsed skills list
def _build_employee_records(rows) -> List[Dict[str, Any]]:
    employees: List[Dict[str, Any]] = []
    employee_ids = [employee_id for employee_id, _, _ in rows]
    if not employee_ids:
        return employees

    conn = get_connection()
    cur = conn.cursor()
    try:
        technical_map = {employee_id: [] for employee_id in employee_ids}
        soft_map = {employee_id: [] for employee_id in employee_ids}
        goal_map = {employee_id: [] for employee_id in employee_ids}
        growth_map = {employee_id: None for employee_id in employee_ids}
        workload_map = {employee_id: 0.0 for employee_id in employee_ids}

        cur.execute(
            """
            SELECT employee_id, skill_name, years_experience, skill_type
            FROM "EmployeeSkills"
            WHERE employee_id = ANY(%s)
            ORDER BY employee_id ASC, skill_name ASC;
            """,
            (employee_ids,),
        )
        for employee_id, skill_name, years_experience, skill_type in cur.fetchall():
            target = technical_map if skill_type == "technical" else soft_map
            target.setdefault(employee_id, []).append(
                {"skill_name": skill_name, "years_experience": years_experience}
            )

        cur.execute(
            """
            SELECT employee_id, skill_name, priority
            FROM "EmployeeLearningGoals"
            WHERE employee_id = ANY(%s)
            ORDER BY employee_id ASC, priority DESC, skill_name ASC;
            """,
            (employee_ids,),
        )
        for employee_id, skill_name, priority in cur.fetchall():
            goal_map.setdefault(employee_id, []).append(
                {"skill_name": skill_name, "priority": priority}
            )

        cur.execute(
            """
            SELECT employee_id, growth_text
            FROM "EmployeePreferences"
            WHERE employee_id = ANY(%s);
            """,
            (employee_ids,),
        )
        for employee_id, growth_text in cur.fetchall():
            growth_map[employee_id] = growth_text

        cur.execute(
            """
            SELECT employee_id, COALESCE(SUM(COALESCE(total_hours, 0)), 0)
            FROM "Assignments"
            WHERE employee_id = ANY(%s)
              AND end_date >= CURRENT_DATE - 90
            GROUP BY employee_id;
            """,
            (employee_ids,),
        )
        for employee_id, total_hours in cur.fetchall():
            workload_map[employee_id] = workload_map.get(employee_id, 0.0) + float(total_hours or 0)

        cur.execute(
            """
            SELECT employee_id, COALESCE(SUM(COALESCE(total_hours, 0)), 0)
            FROM "AssignmentHistory"
            WHERE employee_id = ANY(%s)
              AND end_date >= CURRENT_DATE - 90
            GROUP BY employee_id;
            """,
            (employee_ids,),
        )
        for employee_id, total_hours in cur.fetchall():
            workload_map[employee_id] = workload_map.get(employee_id, 0.0) + float(total_hours or 0)
    finally:
        cur.close()
        conn.close()

    for employee_id, name, role in rows:
        skills = _merge_skills(technical_map.get(employee_id, []))
        soft_skills = _merge_skills(soft_map.get(employee_id, []))

        derived = _derive_role_tags(role)
        skill_names = {s["skill_name"].lower() for s in skills}
        for tag in derived:
            if tag.lower() not in skill_names:
                skills.append({"skill_name": tag, "years_experience": None, "derived": True})
                skill_names.add(tag.lower())

        years = [s["years_experience"] for s in skills if s.get("years_experience") is not None]
        goals = goal_map.get(employee_id, [])
        employees.append({
            "employee_id": employee_id,
            "name": name,
            "role": role,
            "experience": max(years) if years else 0,
            "skills": [s["skill_name"] for s in skills],
            "skills_detail": skills,
            "soft_skills": [s["skill_name"] for s in soft_skills],
            "soft_skills_detail": soft_skills,
            "learning_goals": [g["skill_name"] for g in goals],
            "growth_text": growth_map.get(employee_id),
            "recent_workload_hours": workload_map.get(employee_id, 0.0),
        })

    return employees


def fetch_employees_by_upload(upload_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT employee_id, name, role
            FROM "Employees"
            WHERE upload_id = %s
        """, (upload_id,))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return _build_employee_records(rows)


# ----------------------------------------------------------
# fetch employees for a given user
# ----------------------------------------------------------
# returns a list of dicts containing:
#   - employee_id
#   - name
#   - role
#   - experience years (defaults to 0 if null)
#   - parsed skills list
def fetch_employees_by_user(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT employee_id, name, role
            FROM "Employees"
            WHERE user_id = %s
        """, (user_id,))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return _build_employee_records(rows)


# ----------------------------------------------------------
# fetch feedback history for an employee
# ----------------------------------------------------------
def fetch_employee_feedback(user_id: int, employee_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                rt.task_description,
                rl.performance_rating,
                rl.feedback_notes
            FROM "RecommendationLog" rl
            JOIN "RecommendationTasks" rt ON rl.task_id = rt.task_id
            WHERE rt.user_id = %s
              AND rl.employee_id = %s
              AND rl.manager_selected = TRUE
              AND rl.performance_rating IS NOT NULL
            ORDER BY COALESCE(rl.feedback_at, rl.created_at) DESC
            LIMIT %s;
            """,
            (user_id, employee_id, int(limit)),
        )
        return [
            {
                "task_description": row[0],
                "performance_rating": row[1],
                "feedback_notes": row[2],
            }
            for row in cur.fetchall()
        ]
    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------
# calculate assignment-based availability ratio (0 → 1)
# ----------------------------------------------------------
# logic:
#   - find assignments that overlap with the requested [start, end] window
#   - sum remaining_hours and total_hours from all overlapping rows
#   - if no assignments, availability = 1.0 (fully free)
#   - if total_hours = 0, treat as fully available
#   - return ratio: remaining_hours / total_hours
def calculate_assignment_availability(employee_id: int, start, end) -> float:
    if isinstance(start, str):
        start = datetime.fromisoformat(start).date()
    if isinstance(end, str):
        end = datetime.fromisoformat(end).date()
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT start_date, end_date, total_hours, remaining_hours
            FROM "Assignments"
            WHERE employee_id = %s
              AND start_date <= %s
              AND end_date >= %s
        """, (employee_id, end, start))
        rows = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    availability = calculate_availability_from_rows(
        [(None, row[0], row[1], row[2], row[3]) for row in rows],
        start,
        end,
    )
    return max(0.0, min(1.0, (availability["percent"] / 100.0)))
