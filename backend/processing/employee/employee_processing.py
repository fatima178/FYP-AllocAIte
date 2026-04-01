from typing import Any, Dict, List

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
        skill_type = str(item.get("skill_type") or "technical").strip().lower()
        if skill_type not in ("technical", "soft"):
            raise EmployeeProcessingError(400, "skill_type must be technical or soft")
        normalized = normalize_skill_entry(
            item.get("skill_name"),
            item.get("years_experience"),
        )
        normalized["skill_type"] = skill_type
        skills.append(
            normalized
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

        employee_ids = [row[0] for row in rows]
        skill_map = {employee_id: [] for employee_id in employee_ids}
        goal_map = {employee_id: [] for employee_id in employee_ids}

        if employee_ids:
            cur.execute(
                """
                SELECT employee_id, skill_name, years_experience, skill_type
                FROM "EmployeeSkills"
                WHERE employee_id = ANY(%s)
                ORDER BY employee_id ASC, skill_name ASC;
                """,
                (employee_ids,),
            )
            for employee_id, skill_name, years_experience, skill_type in cur.fetchall():
                skill_map.setdefault(employee_id, []).append(
                    {
                        "skill_name": skill_name,
                        "years_experience": years_experience,
                        "skill_type": skill_type,
                    }
                )

            cur.execute(
                """
                SELECT employee_id, skill_name, priority
                FROM "EmployeeLearningGoals"
                WHERE employee_id = ANY(%s)
                ORDER BY employee_id ASC, priority DESC, skill_name ASC;
                """,
                (employee_ids,),
            )
            for employee_id, skill_name, priority in cur.fetchall():
                goal_map.setdefault(employee_id, []).append(
                    {
                        "skill_name": skill_name,
                        "priority": priority,
                    }
                )

        return [
            {
                "employee_id": employee_id,
                "name": name,
                "role": role,
                "department": department,
                "skills": skill_map.get(employee_id, []),
                "learning_goals": goal_map.get(employee_id, []),
            }
            for employee_id, name, role, department in rows
        ]
    finally:
        cur.close()
        conn.close()


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
                INSERT INTO "EmployeeSkills" (employee_id, skill_name, years_experience, skill_type)
                VALUES (%s, %s, %s, %s);
                """,
                (employee_id, item["skill_name"], item["years_experience"], item["skill_type"]),
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


def add_skills_to_employee(user_id: int, employee_id: int, raw_skills) -> Dict[str, Any]:
    skills = _parse_skills(raw_skills)
    if not skills:
        raise EmployeeProcessingError(400, "at least one skill is required")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT 1
            FROM "Employees"
            WHERE employee_id = %s
              AND user_id = %s;
            """,
            (employee_id, user_id),
        )
        if not cur.fetchone():
            raise EmployeeProcessingError(404, "employee not found for this user")

        upserted = 0
        for item in skills:
            cur.execute(
                """
                SELECT id
                FROM "EmployeeSkills"
                WHERE employee_id = %s
                  AND LOWER(skill_name) = LOWER(%s)
                  AND skill_type = %s;
                """,
                (employee_id, item["skill_name"], item["skill_type"]),
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE "EmployeeSkills"
                    SET years_experience = %s
                    WHERE id = %s;
                    """,
                    (item["years_experience"], row[0]),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO "EmployeeSkills" (employee_id, skill_name, years_experience, skill_type)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (employee_id, item["skill_name"], item["years_experience"], item["skill_type"]),
                )
            upserted += 1

        conn.commit()
        return {"employee_id": employee_id, "skill_count": upserted}
    except EmployeeProcessingError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise EmployeeProcessingError(500, str(exc))
    finally:
        cur.close()
        conn.close()
