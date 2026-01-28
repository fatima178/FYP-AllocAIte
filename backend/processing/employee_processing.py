import json
from typing import Any, Dict, List, Optional

from db import get_connection


class EmployeeProcessingError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _parse_skills(raw) -> List[str]:
    if isinstance(raw, list):
        return [str(s).strip() for s in raw if str(s).strip()]
    if isinstance(raw, str):
        return [s.strip() for s in raw.split(",") if s.strip()]
    return []


def list_employees(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT employee_id, name, role, department, experience_years, skills
            FROM "Employees"
            WHERE user_id = %s
            ORDER BY name ASC;
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    results = []
    for row in rows:
        skills = []
        if isinstance(row[6], str):
            try:
                skills = json.loads(row[6])
            except Exception:
                skills = []
        elif isinstance(row[6], list):
            skills = row[6]
        results.append({
            "employee_id": row[0],
            "name": row[1],
            "role": row[2],
            "department": row[3],
            "experience_years": row[4],
            "skills": skills,
        })
    return results


def create_employee_entry(user_id: int, payload: Dict[str, Any]):
    name = str(payload.get("name") or "").strip()
    role = str(payload.get("role") or "").strip()
    department = str(payload.get("department") or "").strip()
    if not name:
        raise EmployeeProcessingError(400, "name is required")
    if not role:
        raise EmployeeProcessingError(400, "role is required")
    if not department:
        raise EmployeeProcessingError(400, "department is required")
    skills = _parse_skills(payload.get("skills"))
    experience_years = float(payload.get("experience_years") or 0)
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO "Employees" (
                user_id,
                name,
                role,
                department,
                experience_years,
                skills
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING employee_id;
            """,
            (
                user_id,
                name,
                role,
                department,
                experience_years,
                json.dumps(skills),
            ),
        )
        employee_id = cur.fetchone()[0]
        conn.commit()
        return {"employee_id": employee_id}

    except EmployeeProcessingError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise EmployeeProcessingError(500, str(exc))
    finally:
        cur.close()
        conn.close()
