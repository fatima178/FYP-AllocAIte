"""database access helpers for recommendation related processing."""

from datetime import date, datetime
from typing import Any, Dict, List

from db import get_connection


# ----------------------------------------------------------
# fetch skills for a given employee
# ----------------------------------------------------------
# returns list of dicts with per-skill experience
def _fetch_employee_skills(cur, employee_id: int) -> List[Dict[str, Any]]:
    cur.execute(
        """
        SELECT skill_name, years_experience
        FROM "EmployeeSkills"
        WHERE employee_id = %s
        ORDER BY skill_name ASC;
        """,
        (employee_id,),
    )
    return [{"skill_name": s, "years_experience": y} for s, y in cur.fetchall()]


# ----------------------------------------------------------
# fetch employees for a given upload
# ----------------------------------------------------------
# returns a list of dicts containing:
#   - employee_id
#   - name
#   - role
#   - experience years (defaults to 0 if null)
#   - parsed skills list
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

    employees: List[Dict[str, Any]] = []

    for employee_id, name, role in rows:
        conn_skills = get_connection()
        cur_skills = conn_skills.cursor()
        try:
            skills = _fetch_employee_skills(cur_skills, employee_id)
        finally:
            cur_skills.close()
            conn_skills.close()
        years = [s["years_experience"] for s in skills if s.get("years_experience") is not None]
        employees.append({
            "employee_id": employee_id,
            "name": name,
            "role": role,
            "experience": max(years) if years else 0,
            "skills": [s["skill_name"] for s in skills],
        })

    return employees


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

    employees: List[Dict[str, Any]] = []

    for employee_id, name, role in rows:
        conn_skills = get_connection()
        cur_skills = conn_skills.cursor()
        try:
            skills = _fetch_employee_skills(cur_skills, employee_id)
        finally:
            cur_skills.close()
            conn_skills.close()
        years = [s["years_experience"] for s in skills if s.get("years_experience") is not None]
        employees.append({
            "employee_id": employee_id,
            "name": name,
            "role": role,
            "experience": max(years) if years else 0,
            "skills": [s["skill_name"] for s in skills],
        })

    return employees


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
            SELECT start_date, end_date, remaining_hours, total_hours
            FROM "Assignments"
            WHERE employee_id = %s
              AND start_date <= %s
              AND end_date >= %s
        """, (employee_id, end, start))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    # no overlapping assignments → fully available
    if not rows:
        return 1.0

    total_hours = 0.0
    remaining_hours = 0.0

    for start_date, end_date, remaining, total in rows:
        try:
            total = float(total or 0)
        except:
            total = 0
        try:
            remaining = float(remaining or 0)
        except:
            remaining = 0

        assignment_days = (end_date - start_date).days + 1
        window_days = (min(end_date, end) - max(start_date, start)).days + 1
        if assignment_days <= 0 or window_days <= 0:
            continue

        base_hours = remaining if remaining > 0 else total
        if base_hours <= 0:
            base_hours = float(assignment_days * 8)

        hours_per_day = base_hours / assignment_days
        total_hours += base_hours
        remaining_hours += hours_per_day * window_days

    window_days = (end - start).days + 1
    window_capacity = float(window_days) * 8
    if window_capacity <= 0:
        return 0.0

    availability = 1 - (remaining_hours / window_capacity)
    return max(0.0, min(1.0, availability))
