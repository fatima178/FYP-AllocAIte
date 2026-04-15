from typing import Any, Dict

from db import get_connection
from processing.employee.employee_profile_common import EmployeeProfileError, _resolve_employee_id


def _normalize_goal_entry(item: Dict[str, Any]) -> Dict[str, Any]:
    # clean one learning-goal row before saving it
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
    # replace the employee's learning goals with the latest submitted list
    employee_id = _resolve_employee_id(user_id)
    if not isinstance(goals_raw, list):
        raise EmployeeProfileError(400, "learning_goals must be a list")
    goals = [] if not goals_raw else [_normalize_goal_entry(item) for item in goals_raw if isinstance(item, dict)]

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM "EmployeeLearningGoals" WHERE employee_id = %s;', (employee_id,))
        for goal in goals:
            # insert each goal after clearing the old set
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
    # save employee preference/growth text used as a recommendation signal
    employee_id = _resolve_employee_id(user_id)
    preferred_roles = None
    preferred_departments = None
    preferred_projects = None
    work_style = None
    growth_text = None

    if isinstance(payload, str):
        # old frontend shape sent one text field, so still accept it
        growth_text = payload.strip() or None
    elif isinstance(payload, dict):
        preferred_roles = str(payload.get("preferred_roles") or "").strip() or None
        preferred_departments = str(payload.get("preferred_departments") or "").strip() or None
        preferred_projects = str(payload.get("preferred_projects") or "").strip() or None
        work_style = str(payload.get("work_style") or "").strip() or None
        growth_text = str(payload.get("growth_text") or "").strip() or None
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
