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
            select employee_id, name, role, experience_years, skills
            from employees
            where upload_id = %s
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
            select remaining_hours, total_hours
            from assignments
            where employee_id = %s
              and start_date <= %s
              and end_date >= %s
        """, (employee_id, end, start))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    # no overlapping assignments → fully available
    if not rows:
        return 1.0

    # aggregate hours, ignoring null fields
    remaining = sum([r[0] for r in rows if r[0] is not None])
    total = sum([r[1] for r in rows if r[1] is not None])

    # if no valid total hours, assume employee is available
    if total == 0:
        return 1.0

    # clamp to [0.0, 1.0]
    return max(0.0, min(1.0, remaining / total))
