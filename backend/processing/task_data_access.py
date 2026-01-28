"""database access helpers for recommendation related processing."""

import json
from typing import Any, Dict, List

from db import get_connection


# ----------------------------------------------------------
# normalise raw skill data into a clean python list
# ----------------------------------------------------------
# skills may be stored as:
#   - json string
#   - python list/tuple
#   - bytes (rare, legacy export formats)
# this function ensures we always return a list[str] with no empty entries.
def _parse_skills(raw_skills: Any) -> List[str]:
    if isinstance(raw_skills, bytes):
        # decode database byte strings
        raw_skills = raw_skills.decode("utf-8")

    if isinstance(raw_skills, str):
        # attempt to parse json list
        try:
            value = json.loads(raw_skills)
        except Exception:
            value = []
    elif isinstance(raw_skills, (list, tuple)):
        # already list-like
        value = list(raw_skills)
    else:
        # unknown format - empty list
        value = []

    # clean final output: remove blank values, convert everything to strings
    return [str(skill).strip() for skill in value if str(skill).strip()]


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
            SELECT employee_id, name, role, experience_years, skills
            FROM "Employees"
            WHERE upload_id = %s
        """, (upload_id,))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    employees: List[Dict[str, Any]] = []

    for employee_id, name, role, experience_years, skills in rows:
        employees.append({
            "employee_id": employee_id,
            "name": name,
            "role": role,
            "experience": experience_years or 0,
            "skills": _parse_skills(skills),
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
            SELECT employee_id, name, role, experience_years, skills
            FROM "Employees"
            WHERE user_id = %s
        """, (user_id,))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    employees: List[Dict[str, Any]] = []

    for employee_id, name, role, experience_years, skills in rows:
        employees.append({
            "employee_id": employee_id,
            "name": name,
            "role": role,
            "experience": experience_years or 0,
            "skills": _parse_skills(skills),
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
