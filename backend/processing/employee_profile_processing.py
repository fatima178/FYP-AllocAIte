import hashlib
import re
from datetime import date
from typing import Any, Dict, List

from db import get_connection
from processing.employee_processing import EmployeeProcessingError, normalize_skill_entry
from processing.assignment_history_processing import archive_completed_assignments
from processing.nlp.task_matching import match_employees
from processing.settings_processing import fetch_user_settings
from datetime import datetime


class EmployeeProfileError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _resolve_employee_id(user_id: int) -> int:
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


def _fetch_self_skills(cur, employee_id: int) -> List[Dict[str, Any]]:
    cur.execute(
        """
        SELECT skill_name, years_experience
        FROM "EmployeeSelfSkills"
        WHERE employee_id = %s
        ORDER BY skill_name ASC;
        """,
        (employee_id,),
    )
    return [{"skill_name": s, "years_experience": y} for s, y in cur.fetchall()]


def _fetch_learning_goals(cur, employee_id: int) -> List[Dict[str, Any]]:
    cur.execute(
        """
        SELECT skill_name, priority, notes
        FROM "EmployeeLearningGoals"
        WHERE employee_id = %s
        ORDER BY priority DESC, skill_name ASC;
        """,
        (employee_id,),
    )
    return [
        {"skill_name": s, "priority": p, "notes": n}
        for s, p, n in cur.fetchall()
    ]


def _fetch_preferences(cur, employee_id: int) -> Dict[str, Any]:
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
    today = date.today()

    cur.execute(
        """
        SELECT assignment_id, title, start_date, end_date, total_hours, remaining_hours, priority
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
            "priority": row[6],
        }
        if row[3] and row[3] < today:
            past_assignments.append(payload)
        else:
            assignments.append(payload)

    cur.execute(
        """
        SELECT title, start_date, end_date, total_hours, remaining_hours, priority, archived_at
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
            "priority": row[5],
            "archived_at": row[6].isoformat() if row[6] else None,
        }
        for row in cur.fetchall()
    ]

    return {
        "current_assignments": assignments,
        "past_assignments": past_assignments,
        "history": history,
    }


def get_employee_profile(user_id: int) -> Dict[str, Any]:
    employee_id = _resolve_employee_id(user_id)
    archive_completed_assignments(user_id)
    conn = get_connection()
    cur = conn.cursor()
    try:
        record = _fetch_employee_record(cur, employee_id)
        org_skills = _fetch_employee_skills(cur, employee_id)
        self_skills = _fetch_self_skills(cur, employee_id)
        learning_goals = _fetch_learning_goals(cur, employee_id)
        preferences = _fetch_preferences(cur, employee_id)
        assignments = _fetch_assignments(cur, employee_id)

        return {
            **record,
            "org_skills": org_skills,
            "self_skills": self_skills,
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
        manager_name = row[0] if row else None
        manager_email = row[1] if row else None

        return {
            **base,
            "manager_name": manager_name,
            "manager_email": manager_email,
        }
    finally:
        cur.close()
        conn.close()


def _normalize_skill_list(skills_raw) -> List[Dict[str, Any]]:
    if not isinstance(skills_raw, list):
        raise EmployeeProfileError(400, "skills must be a list")
    if not skills_raw:
        return []
    skills = []
    for item in skills_raw:
        if not isinstance(item, dict):
            continue
        try:
            skills.append(normalize_skill_entry(item.get("skill_name"), item.get("years_experience")))
        except EmployeeProcessingError as exc:
            raise EmployeeProfileError(exc.status_code, exc.message)
    return skills


def update_employee_self_skills(user_id: int, skills_raw) -> Dict[str, Any]:
    employee_id = _resolve_employee_id(user_id)
    skills = _normalize_skill_list(skills_raw)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'DELETE FROM "EmployeeSelfSkills" WHERE employee_id = %s;',
            (employee_id,),
        )
        for item in skills:
            cur.execute(
                """
                INSERT INTO "EmployeeSelfSkills" (employee_id, skill_name, years_experience)
                VALUES (%s, %s, %s);
                """,
                (employee_id, item["skill_name"], item["years_experience"]),
            )
        conn.commit()
        return {"employee_id": employee_id, "skill_count": len(skills)}
    except EmployeeProfileError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise EmployeeProfileError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def _normalize_goal_entry(item: Dict[str, Any]) -> Dict[str, Any]:
    clean_name = str(item.get("skill_name") or "").strip()
    if not clean_name:
        raise EmployeeProfileError(400, "skill_name is required for learning goals")
    priority_raw = item.get("priority", 3)
    try:
        priority = int(priority_raw)
    except Exception:
        raise EmployeeProfileError(400, "priority must be an integer")
    priority = max(1, min(5, priority))
    notes = str(item.get("notes") or "").strip() or None
    return {"skill_name": clean_name, "priority": priority, "notes": notes}


def update_learning_goals(user_id: int, goals_raw) -> Dict[str, Any]:
    employee_id = _resolve_employee_id(user_id)
    if not isinstance(goals_raw, list):
        raise EmployeeProfileError(400, "learning_goals must be a list")
    if not goals_raw:
        goals = []
    else:
        goals = [_normalize_goal_entry(item) for item in goals_raw if isinstance(item, dict)]

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'DELETE FROM "EmployeeLearningGoals" WHERE employee_id = %s;',
            (employee_id,),
        )
        for goal in goals:
            cur.execute(
                """
                INSERT INTO "EmployeeLearningGoals" (employee_id, skill_name, priority, notes)
                VALUES (%s, %s, %s, %s);
                """,
                (employee_id, goal["skill_name"], goal["priority"], goal["notes"]),
            )
        conn.commit()
        return {"employee_id": employee_id, "goal_count": len(goals)}
    except EmployeeProfileError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise EmployeeProfileError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def update_preferences(user_id: int, payload) -> Dict[str, Any]:
    employee_id = _resolve_employee_id(user_id)
    preferred_roles = None
    preferred_departments = None
    preferred_projects = None
    work_style = None
    growth_text = None

    if isinstance(payload, str):
        growth_text = payload.strip() or None
    elif isinstance(payload, dict):
        preferred_roles = str(payload.get("preferred_roles") or "").strip() or None
        preferred_departments = str(payload.get("preferred_departments") or "").strip() or None
        preferred_projects = str(payload.get("preferred_projects") or "").strip() or None
        work_style = str(payload.get("work_style") or "").strip() or None
        growth_value = payload.get("growth_text") if "growth_text" in payload else payload.get("preferences_text")
        growth_text = str(growth_value or "").strip() or None
    else:
        raise EmployeeProfileError(400, "preferences must be an object or string")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO "EmployeePreferences" (
                employee_id,
                preferred_roles,
                preferred_departments,
                preferred_projects,
                growth_text,
                work_style
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (employee_id)
            DO UPDATE SET
                preferred_roles = EXCLUDED.preferred_roles,
                preferred_departments = EXCLUDED.preferred_departments,
                preferred_projects = EXCLUDED.preferred_projects,
                growth_text = EXCLUDED.growth_text,
                work_style = EXCLUDED.work_style,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (
                employee_id,
                preferred_roles,
                preferred_departments,
                preferred_projects,
                growth_text,
                work_style,
            ),
        )
        conn.commit()
        return {"employee_id": employee_id}
    except Exception as exc:
        conn.rollback()
        raise EmployeeProfileError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def _validate_password(password: str):
    if not (re.search(r"[A-Z]", password) and re.search(r"[^A-Za-z0-9]", password)):
        raise EmployeeProfileError(
            400,
            "password must include at least one uppercase letter and one special character.",
        )


def create_employee_account(
    manager_user_id: int,
    employee_id: int,
    name: str,
    email: str,
    password: str,
) -> Dict[str, Any]:
    clean_name = str(name or "").strip()
    clean_email = str(email or "").strip().lower()
    if not clean_name:
        raise EmployeeProfileError(400, "name is required")
    if not clean_email:
        raise EmployeeProfileError(400, "email is required")
    _validate_password(password)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT 1
            FROM "Employees"
            WHERE employee_id = %s AND user_id = %s;
            """,
            (employee_id, manager_user_id),
        )
        if not cur.fetchone():
            raise EmployeeProfileError(404, "employee not found for this user")

        cur.execute(
            'SELECT 1 FROM "Users" WHERE email = %s;',
            (clean_email,),
        )
        if cur.fetchone():
            raise EmployeeProfileError(400, "email already registered.")

        cur.execute(
            'SELECT 1 FROM "Users" WHERE employee_id = %s;',
            (employee_id,),
        )
        if cur.fetchone():
            raise EmployeeProfileError(400, "employee already has a login")

        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        cur.execute(
            """
            INSERT INTO "Users" (name, email, password_hash, account_type, employee_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id;
            """,
            (clean_name, clean_email, password_hash, "employee", employee_id),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return {"user_id": user_id, "employee_id": employee_id}

    except EmployeeProfileError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise EmployeeProfileError(500, str(exc))
    finally:
        cur.close()
        conn.close()
