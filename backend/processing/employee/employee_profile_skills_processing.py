from typing import Any, Dict, List

from db import get_connection
from processing.employee.employee_processing import (
    EmployeeProcessingError,
    normalize_skill_entry,
)
from processing.employee.employee_profile_common import (
    EmployeeProfileError,
    _ensure_manager_user,
    _resolve_employee_id,
    _upsert_employee_skill,
)


def _normalize_skill_list(skills_raw) -> List[Dict[str, Any]]:
    # clean employee-submitted skills before they are saved as pending requests
    if not isinstance(skills_raw, list):
        raise EmployeeProfileError(400, "skills must be a list")
    if not skills_raw:
        return []
    skills = []
    for item in skills_raw:
        if not isinstance(item, dict):
            continue
        try:
            cleaned = normalize_skill_entry(item.get("skill_name"), item.get("years_experience"))
            skill_type = str(item.get("skill_type") or "technical").strip().lower()
            if skill_type not in ("technical", "soft"):
                raise EmployeeProfileError(400, "skill_type must be technical or soft")
            cleaned["skill_type"] = skill_type
            skills.append(cleaned)
        except EmployeeProcessingError as exc:
            raise EmployeeProfileError(exc.status_code, exc.message)
    return skills


def update_employee_self_skills(user_id: int, skills_raw) -> Dict[str, Any]:
    # employee changes do not immediately affect recommendations until approved
    employee_id = _resolve_employee_id(user_id)
    skills = _normalize_skill_list(skills_raw)
    conn = get_connection()
    cur = conn.cursor()
    try:
        for item in skills:
            cur.execute(
                """
                SELECT id
                FROM "EmployeeSelfSkills"
                WHERE employee_id = %s
                  AND LOWER(skill_name) = LOWER(%s)
                  AND skill_type = %s
                  AND status = 'pending';
                """,
                (employee_id, item["skill_name"], item["skill_type"]),
            )
            row = cur.fetchone()
            if row:
                # update an existing pending request instead of making duplicates
                cur.execute(
                    """
                    UPDATE "EmployeeSelfSkills"
                    SET years_experience = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                    """,
                    (item["years_experience"], row[0]),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO "EmployeeSelfSkills" (
                        employee_id,
                        skill_name,
                        years_experience,
                        skill_type,
                        status
                    )
                    VALUES (%s, %s, %s, %s, 'pending');
                    """,
                    (employee_id, item["skill_name"], item["years_experience"], item["skill_type"]),
                )
        conn.commit()
        return {"employee_id": employee_id, "skill_count": len(skills), "status": "pending"}
    except EmployeeProfileError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise EmployeeProfileError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def delete_employee_skill(user_id: int, skill_name: str, skill_type: str) -> Dict[str, Any]:
    # employees can remove skills from their approved profile
    employee_id = _resolve_employee_id(user_id)
    clean_name = str(skill_name or "").strip()
    if not clean_name:
        raise EmployeeProfileError(400, "skill_name is required")
    clean_type = str(skill_type or "").strip().lower()
    if clean_type not in ("technical", "soft"):
        raise EmployeeProfileError(400, "skill_type must be technical or soft")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            DELETE FROM "EmployeeSkills"
            WHERE employee_id = %s
              AND LOWER(skill_name) = LOWER(%s)
              AND skill_type = %s;
            """,
            (employee_id, clean_name, clean_type),
        )
        deleted = cur.rowcount or 0
        conn.commit()
        return {"employee_id": employee_id, "deleted": deleted}
    except Exception as exc:
        conn.rollback()
        raise EmployeeProfileError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def fetch_pending_skill_requests(manager_user_id: int) -> Dict[str, Any]:
    # manager dashboard uses this to review employee-submitted skills
    conn = get_connection()
    cur = conn.cursor()
    try:
        _ensure_manager_user(cur, manager_user_id)
        cur.execute(
            """
            SELECT
                ess.id,
                ess.skill_name,
                ess.years_experience,
                ess.skill_type,
                ess.updated_at,
                e.employee_id,
                e.name
            FROM "EmployeeSelfSkills" ess
            JOIN "Employees" e ON e.employee_id = ess.employee_id
            WHERE e.user_id = %s
              AND ess.status = 'pending'
            ORDER BY ess.updated_at DESC, e.name ASC;
            """,
            (manager_user_id,),
        )
        return {
            "pending_skill_requests": [
                {
                    "request_id": row[0],
                    "skill_name": row[1],
                    "years_experience": row[2],
                    "skill_type": row[3],
                    "updated_at": row[4].isoformat() if row[4] else None,
                    "employee_id": row[5],
                    "employee_name": row[6],
                }
                for row in cur.fetchall()
            ]
        }
    finally:
        cur.close()
        conn.close()


def review_pending_skill_request(manager_user_id: int, request_id: int, approve: bool) -> Dict[str, Any]:
    # approving copies the skill into EmployeeSkills; rejecting only updates request status
    conn = get_connection()
    cur = conn.cursor()
    try:
        _ensure_manager_user(cur, manager_user_id)
        cur.execute(
            """
            SELECT ess.employee_id, ess.skill_name, ess.years_experience, ess.skill_type, ess.status
            FROM "EmployeeSelfSkills" ess
            JOIN "Employees" e ON e.employee_id = ess.employee_id
            WHERE ess.id = %s
              AND e.user_id = %s;
            """,
            (request_id, manager_user_id),
        )
        request = cur.fetchone()
        if not request:
            raise EmployeeProfileError(404, "skill request not found")

        employee_id, skill_name, years_experience, skill_type, status = request
        if status != "pending":
            raise EmployeeProfileError(400, "skill request has already been reviewed")

        if approve:
            # approved skills start affecting recommendations straight away
            _upsert_employee_skill(cur, employee_id, skill_name, years_experience, skill_type)
            cur.execute(
                """
                UPDATE "EmployeeSelfSkills"
                SET status = 'approved',
                    approved_by_user_id = %s,
                    approved_at = CURRENT_TIMESTAMP,
                    rejected_at = NULL
                WHERE id = %s;
                """,
                (manager_user_id, request_id),
            )
            final_status = "approved"
        else:
            cur.execute(
                """
                UPDATE "EmployeeSelfSkills"
                SET status = 'rejected',
                    approved_by_user_id = %s,
                    approved_at = NULL,
                    rejected_at = CURRENT_TIMESTAMP
                WHERE id = %s;
                """,
                (manager_user_id, request_id),
            )
            final_status = "rejected"

        conn.commit()
        return {"request_id": request_id, "status": final_status}
    except EmployeeProfileError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise EmployeeProfileError(500, str(exc))
    finally:
        cur.close()
        conn.close()
