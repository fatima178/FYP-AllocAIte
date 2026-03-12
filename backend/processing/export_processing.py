from io import BytesIO

import pandas as pd

from db import get_connection


EXPORT_COLUMNS = [
    "Employee Name",
    "Role",
    "Department",
    "Skill Set",
    "Skill Experience (Years)",
    "Skill Level (1–5)",
    "Current Project",
    "Start Date",
    "End Date",
    "Total Hours",
    "Remaining Hours",
    "Soft Skill Set",
    "Soft Skill Experience (Years)",
]


def _join_list(values):
    return ", ".join(str(v) for v in values if v not in (None, "")) if values else ""


def export_manager_data(user_id: int) -> bytes:
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
        employees = cur.fetchall()

        if not employees:
            df = pd.DataFrame(columns=EXPORT_COLUMNS)
            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            return buffer.getvalue()

        emp_ids = [row[0] for row in employees]

        cur.execute(
            """
            SELECT employee_id, skill_name, years_experience, skill_type
            FROM "EmployeeSkills"
            WHERE employee_id = ANY(%s);
            """,
            (emp_ids,),
        )
        skills = cur.fetchall()

        skill_map = {
            emp_id: {
                "technical_names": [],
                "technical_years": [],
                "soft_names": [],
                "soft_years": [],
            }
            for emp_id in emp_ids
        }

        for emp_id, name, years, skill_type in skills:
            entry = skill_map.get(emp_id)
            if not entry:
                continue
            if skill_type == "soft":
                entry["soft_names"].append(name)
                entry["soft_years"].append(years)
            else:
                entry["technical_names"].append(name)
                entry["technical_years"].append(years)

        cur.execute(
            """
            SELECT employee_id, title, start_date, end_date, total_hours, remaining_hours
            FROM "Assignments"
            WHERE employee_id = ANY(%s)
            ORDER BY employee_id, start_date;
            """,
            (emp_ids,),
        )
        assignments = cur.fetchall()

        assignments_by_emp = {}
        for row in assignments:
            assignments_by_emp.setdefault(row[0], []).append(row[1:])

        rows = []
        for emp_id, name, role, department in employees:
            skill_entry = skill_map.get(emp_id) or {}
            tech_names = _join_list(skill_entry.get("technical_names"))
            tech_years = _join_list(skill_entry.get("technical_years"))
            soft_names = _join_list(skill_entry.get("soft_names"))
            soft_years = _join_list(skill_entry.get("soft_years"))

            emp_assignments = assignments_by_emp.get(emp_id) or [None]

            for assignment in emp_assignments:
                if assignment is None:
                    title = ""
                    start_date = ""
                    end_date = ""
                    total_hours = ""
                    remaining_hours = ""
                else:
                    title, start_date, end_date, total_hours, remaining_hours = assignment
                    start_date = str(start_date) if start_date else ""
                    end_date = str(end_date) if end_date else ""

                rows.append({
                    "Employee Name": name,
                    "Role": role,
                    "Department": department,
                    "Skill Set": tech_names,
                    "Skill Experience (Years)": tech_years,
                    "Skill Level (1–5)": "",
                    "Current Project": title,
                    "Start Date": start_date,
                    "End Date": end_date,
                    "Total Hours": total_hours,
                    "Remaining Hours": remaining_hours,
                    "Soft Skill Set": soft_names,
                    "Soft Skill Experience (Years)": soft_years,
                })

        df = pd.DataFrame(rows, columns=EXPORT_COLUMNS)
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        return buffer.getvalue()
    finally:
        cur.close()
        conn.close()
