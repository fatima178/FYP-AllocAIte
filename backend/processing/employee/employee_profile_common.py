from datetime import date
from typing import Any, Dict, List

from db import get_connection


# shared error type for employee portal processing
class EmployeeProfileError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _resolve_employee_id(user_id: int) -> int:
    # convert the logged-in user id into the employee row it belongs to
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'SELECT account_type, employee_id FROM "Users" WHERE user_id = %s;',
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            raise EmployeeProfileError(404, "user not found")
        account_type, employee_id = row
        if account_type != "employee":
            raise EmployeeProfileError(403, "user is not an employee account")
        if not employee_id:
            raise EmployeeProfileError(404, "employee account not linked")
        return int(employee_id)
    finally:
        cur.close()
        conn.close()


def _fetch_employee_record(cur, employee_id: int) -> Dict[str, Any]:
    # basic employee profile data shown at the top of the portal
    cur.execute(
        """
        SELECT employee_id, name, role, department, user_id
        FROM "Employees"
        WHERE employee_id = %s;
        """,
        (employee_id,),
    )
    row = cur.fetchone()
    if not row:
        raise EmployeeProfileError(404, "employee not found")
    return {
        "employee_id": row[0],
        "name": row[1],
        "role": row[2],
        "department": row[3],
        "manager_user_id": row[4],
    }


def _fetch_employee_skills(cur, employee_id: int, skill_type: str) -> List[Dict[str, Any]]:
    # skills are split into technical and soft skills using skill_type
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


def _fetch_pending_self_skills(cur, employee_id: int) -> List[Dict[str, Any]]:
    # pending self-reported skills still need manager approval
    cur.execute(
        """
        SELECT id, skill_name, years_experience, skill_type, status, updated_at
        FROM "EmployeeSelfSkills"
        WHERE employee_id = %s
          AND status = 'pending'
        ORDER BY updated_at DESC, skill_name ASC;
        """,
        (employee_id,),
    )
    return [
        {
            "request_id": row[0],
            "skill_name": row[1],
            "years_experience": row[2],
            "skill_type": row[3],
            "status": row[4],
            "updated_at": row[5].isoformat() if row[5] else None,
        }
        for row in cur.fetchall()
    ]


def _fetch_learning_goals(cur, employee_id: int) -> List[Dict[str, Any]]:
    # learning goals help the recommender understand what the employee wants to build
    cur.execute(
        """
        SELECT skill_name, priority, notes
        FROM "EmployeeLearningGoals"
        WHERE employee_id = %s
        ORDER BY priority DESC, skill_name ASC;
        """,
        (employee_id,),
    )
    return [{"skill_name": s, "priority": p, "notes": n} for s, p, n in cur.fetchall()]


def _fetch_preferences(cur, employee_id: int) -> Dict[str, Any]:
    # preference text is optional, so return empty fields when no row exists
    cur.execute(
        """
        SELECT preferred_roles, preferred_departments, preferred_projects, growth_text, work_style
        FROM "EmployeePreferences"
        WHERE employee_id = %s;
        """,
        (employee_id,),
    )
    row = cur.fetchone()
    if not row:
        return {
            "preferred_roles": None,
            "preferred_departments": None,
            "preferred_projects": None,
            "growth_text": None,
            "work_style": None,
        }
    return {
        "preferred_roles": row[0],
        "preferred_departments": row[1],
        "preferred_projects": row[2],
        "growth_text": row[3],
        "work_style": row[4],
    }


def _fetch_assignments(cur, employee_id: int) -> Dict[str, Any]:
    # split assignments into current/past buckets for the employee portal
    today = date.today()

    cur.execute(
        """
        SELECT assignment_id, title, start_date, end_date, total_hours, remaining_hours
        FROM "Assignments"
        WHERE employee_id = %s
        ORDER BY start_date DESC;
        """,
        (employee_id,),
    )
    assignments = []
    past_assignments = []

    for row in cur.fetchall():
        payload = {
            "assignment_id": row[0],
            "title": row[1],
            "start_date": str(row[2]),
            "end_date": str(row[3]),
            "total_hours": row[4],
            "remaining_hours": row[5],
        }
        if row[3] and row[3] < today:
            past_assignments.append(payload)
        else:
            assignments.append(payload)

    cur.execute(
        """
        SELECT title, start_date, end_date, total_hours, remaining_hours, archived_at
        FROM "AssignmentHistory"
        WHERE employee_id = %s
        ORDER BY end_date DESC;
        """,
        (employee_id,),
    )
    history = [
        {
            "title": row[0],
            "start_date": str(row[1]),
            "end_date": str(row[2]),
            "total_hours": row[3],
            "remaining_hours": row[4],
            "archived_at": row[5].isoformat() if row[5] else None,
        }
        for row in cur.fetchall()
    ]

    return {
        "current_assignments": assignments,
        "past_assignments": past_assignments,
        "history": history,
    }


def _ensure_manager_user(cur, manager_user_id: int) -> None:
    # approval actions should only be available to manager accounts
    cur.execute(
        'SELECT account_type FROM "Users" WHERE user_id = %s;',
        (manager_user_id,),
    )
    row = cur.fetchone()
    if not row:
        raise EmployeeProfileError(404, "user not found")
    if row[0] != "manager":
        raise EmployeeProfileError(403, "user is not a manager account")


def _upsert_employee_skill(cur, employee_id: int, skill_name: str, years_experience, skill_type: str) -> None:
    # update existing skill experience or insert a new skill if it is missing
    cur.execute(
        """
        SELECT id
        FROM "EmployeeSkills"
        WHERE employee_id = %s
          AND LOWER(skill_name) = LOWER(%s)
          AND skill_type = %s;
        """,
        (employee_id, skill_name, skill_type),
    )
    existing = cur.fetchone()
    if existing:
        cur.execute(
            """
            UPDATE "EmployeeSkills"
            SET years_experience = %s
            WHERE id = %s;
            """,
            (years_experience, existing[0]),
        )
        return

    cur.execute(
        """
        INSERT INTO "EmployeeSkills" (employee_id, skill_name, years_experience, skill_type)
        VALUES (%s, %s, %s, %s);
        """,
        (employee_id, skill_name, years_experience, skill_type),
    )
