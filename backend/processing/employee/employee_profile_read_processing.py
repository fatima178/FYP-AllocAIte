from datetime import datetime
from typing import Any, Dict

from db import get_connection
from processing.assignment_history_processing import archive_completed_assignments
from processing.nlp.task_matching import match_employees
from processing.settings.settings_processing import fetch_user_settings
from processing.employee.employee_profile_common import (
    EmployeeProfileError,
    _fetch_assignments,
    _fetch_employee_record,
    _fetch_employee_skills,
    _fetch_learning_goals,
    _fetch_pending_self_skills,
    _fetch_preferences,
    _resolve_employee_id,
)


def get_employee_profile(user_id: int) -> Dict[str, Any]:
    employee_id = _resolve_employee_id(user_id)
    archive_completed_assignments(user_id)
    conn = get_connection()
    cur = conn.cursor()
    try:
        record = _fetch_employee_record(cur, employee_id)
        technical_skills = _fetch_employee_skills(cur, employee_id, "technical")
        soft_skills = _fetch_employee_skills(cur, employee_id, "soft")
        pending_skill_requests = _fetch_pending_self_skills(cur, employee_id)
        learning_goals = _fetch_learning_goals(cur, employee_id)
        preferences = _fetch_preferences(cur, employee_id)
        assignments = _fetch_assignments(cur, employee_id)
        return {
            **record,
            "technical_skills": technical_skills,
            "soft_skills": soft_skills,
            "pending_skill_requests": pending_skill_requests,
            "learning_goals": learning_goals,
            "preferences": preferences,
            **assignments,
        }
    finally:
        cur.close()
        conn.close()


def get_employee_recommendation_reason(
    user_id: int,
    task_description: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    employee_id = _resolve_employee_id(user_id)
    conn = get_connection()
    cur = conn.cursor()
    try:
        record = _fetch_employee_record(cur, employee_id)
        manager_user_id = record["manager_user_id"]
        if not manager_user_id:
            raise EmployeeProfileError(404, "manager account not found")

        try:
            start_dt = datetime.fromisoformat(start_date).date()
            end_dt = datetime.fromisoformat(end_date).date()
        except ValueError:
            raise EmployeeProfileError(400, "start_date and end_date must be valid ISO dates")

        if start_dt > end_dt:
            raise EmployeeProfileError(400, "start_date must be on or before end_date")

        results = match_employees(task_description, manager_user_id, start_dt.isoformat(), end_dt.isoformat())
        if not results:
            return {"message": "no recommendations found for this task"}

        entry = next((item for item in results if item.get("employee_id") == employee_id), None)
        if not entry:
            return {"message": "employee not found in recommendations"}

        return {
            "employee_id": employee_id,
            "reason": entry.get("reason"),
            "score_percent": entry.get("score_percent"),
            "availability_percent": entry.get("availability_percent"),
            "skills": entry.get("skills", []),
            "soft_skills": entry.get("soft_skills", []),
            "learning_goals": entry.get("learning_goals", []),
        }
    finally:
        cur.close()
        conn.close()


def get_employee_settings(user_id: int) -> Dict[str, Any]:
    employee_id = _resolve_employee_id(user_id)
    base = fetch_user_settings(user_id)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT u.name, u.email
            FROM "Employees" e
            LEFT JOIN "Users" u ON e.user_id = u.user_id
            WHERE e.employee_id = %s;
            """,
            (employee_id,),
        )
        row = cur.fetchone()
        return {
            **base,
            "manager_name": row[0] if row else None,
            "manager_email": row[1] if row else None,
        }
    finally:
        cur.close()
        conn.close()
