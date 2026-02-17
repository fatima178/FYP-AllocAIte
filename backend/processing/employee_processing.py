from typing import Any, Dict, List, Optional

from db import get_connection


class EmployeeProcessingError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def normalize_skill_entry(name: str, years) -> Dict[str, Any]:
    clean_name = str(name or "").strip()
    if not clean_name:
        raise EmployeeProcessingError(400, "skill_name is required")
    if years is None or str(years).strip() == "":
        raise EmployeeProcessingError(400, "years_experience is required")
    try:
        clean_years = float(years)
    except Exception:
        raise EmployeeProcessingError(400, "years_experience must be a number")
    return {"skill_name": clean_name, "years_experience": clean_years}


def normalize_skill_lines(raw_text: str) -> List[Dict[str, Any]]:
    text = str(raw_text or "").strip()
    if not text:
        raise EmployeeProcessingError(400, "skills input is required")
    skills = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "," in line:
            name, years = line.split(",", 1)
        elif ":" in line:
            name, years = line.split(":", 1)
        else:
            raise EmployeeProcessingError(400, "each skill line must include a separator")
        skills.append(normalize_skill_entry(name, years))
    if not skills:
        raise EmployeeProcessingError(400, "skills input is required")
    return skills


def _parse_skills(raw) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    skills = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        skills.append(
            normalize_skill_entry(
                item.get("skill_name"),
                item.get("years_experience"),
            )
        )
    return skills


def list_employees(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT employee_id, name, role, department
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
        employee_id = row[0]
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT skill_name, years_experience
                FROM "EmployeeSkills"
                WHERE employee_id = %s
                ORDER BY skill_name ASC;
                """,
                (employee_id,),
            )
            skill_rows = cur.fetchall()
            cur.execute(
                """
                SELECT skill_name, years_experience
                FROM "EmployeeSelfSkills"
                WHERE employee_id = %s
                ORDER BY skill_name ASC;
                """,
                (employee_id,),
            )
            self_rows = cur.fetchall()
            cur.execute(
                """
                SELECT skill_name, priority
                FROM "EmployeeLearningGoals"
                WHERE employee_id = %s
                ORDER BY priority DESC, skill_name ASC;
                """,
                (employee_id,),
            )
            goal_rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        skills = [{"skill_name": s, "years_experience": y} for s, y in skill_rows]
        self_skills = [{"skill_name": s, "years_experience": y} for s, y in self_rows]
        learning_goals = [{"skill_name": s, "priority": p} for s, p in goal_rows]
        results.append({
            "employee_id": employee_id,
            "name": row[1],
            "role": row[2],
            "department": row[3],
            "skills": skills,
            "self_skills": self_skills,
            "learning_goals": learning_goals,
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
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO "Employees" (
                user_id,
                name,
                role,
                department
            )
            VALUES (%s, %s, %s, %s)
            RETURNING employee_id;
            """,
            (
                user_id,
                name,
                role,
                department,
            ),
        )
        employee_id = cur.fetchone()[0]
        for item in skills:
            cur.execute(
                """
                INSERT INTO "EmployeeSkills" (employee_id, skill_name, years_experience)
                VALUES (%s, %s, %s);
                """,
                (employee_id, item["skill_name"], item["years_experience"]),
            )
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
