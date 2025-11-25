# processing/dashboard_processing.py

from datetime import date
from db import get_connection
from processing.availability_processing import calculate_availability, dashboard_window

# get the latest update for user
def get_latest_upload_id(cur, user_id: int):
    cur.execute("""
        SELECT upload_id
        FROM Uploads
        WHERE user_id = %s AND is_active = TRUE
        ORDER BY upload_date DESC
        LIMIT 1;
    """, (user_id,))
    result = cur.fetchone()
    return result[0] if result else None


def get_dashboard_summary(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        upload_id = get_latest_upload_id(cur, user_id)
        if not upload_id:
            return {
                "total_employees": 0,
                "active_projects": 0,
                "available_next_7_days": 0,
                "available_this_week": 0,
            }

        # 1. TOTAL EMPLOYEES
        cur.execute("""
            SELECT COUNT(*) 
            FROM Employees 
            WHERE upload_id = %s;
        """, (upload_id,))
        total_employees = cur.fetchone()[0]

        # 2. ACTIVE PROJECTS (any assignment that's still running today)
        today = date.today()
        cur.execute("""
            SELECT COUNT(*)
            FROM Assignments
            WHERE upload_id = %s
              AND start_date <= %s
              AND end_date >= %s;
        """, (upload_id, today, today))
        active_projects = cur.fetchone()[0]

        # 3. AVAILABLE IN THE NEXT 7 DAYS
        window_start, window_end = dashboard_window()

        cur.execute("""
            SELECT employee_id
            FROM Employees
            WHERE upload_id = %s;
        """, (upload_id,))
        employees = cur.fetchall()

        available_count = 0
        for (employee_id,) in employees:
            result = calculate_availability(employee_id, window_start, window_end)
            if result["status"].lower() == "available":
                available_count += 1

        summary = {
            "total_employees": total_employees,
            "active_projects": active_projects,
            "available_next_7_days": available_count,
        }
        summary["available_this_week"] = summary["available_next_7_days"]
        return summary

    finally:
        cur.close()
        conn.close()


def get_employees_data(user_id: int, search=None, skills=None, availability=None):
    """
    Returns a structured list of employees + dynamic availability + active assignments
    for the next 7 days.
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        upload_id = get_latest_upload_id(cur, user_id)
        if not upload_id:
            return {"employees": []}

        window_start, window_end = dashboard_window()

        # Fetch all employees
        cur.execute("""
            SELECT employee_id, name, role, department, experience_years, skills
            FROM Employees
            WHERE upload_id = %s
            ORDER BY name ASC;
        """, (upload_id,))
        rows = cur.fetchall()

        employees = []
        for emp in rows:
            employee_id, name, role, dept, exp, skills_json = emp

            parsed_skills = []
            if isinstance(skills_json, list):
                parsed_skills = skills_json
            elif isinstance(skills_json, str):
                try:
                    import json
                    parsed_skills = json.loads(skills_json)
                except:
                    parsed_skills = []

            # apply search filter
            if search:
                st = search.lower()
                if st not in name.lower() and st not in role.lower():
                    continue

            # apply skill filter
            if skills:
                lower_emp = [s.lower() for s in parsed_skills]
                lower_filt = [s.lower() for s in skills]
                if not all(s in lower_emp for s in lower_filt):
                    continue

            # AVAILABILITY FOR NEXT 7 DAYS
            availability_obj = calculate_availability(employee_id, window_start, window_end)

            # AVAILABILITY FILTER
            if availability:
                if availability_obj["status"].lower() != availability.lower():
                    continue

            # FETCH ACTIVE ASSIGNMENTS FOR DISPLAY
            today = date.today()
            cur.execute("""
                SELECT title, start_date, end_date, priority
                FROM Assignments
                WHERE employee_id = %s
                  AND start_date <= %s
                  AND end_date >= %s;
            """, (employee_id, today, today))
            assignments = []
            for title, start_d, end_d, priority in cur.fetchall():
                assignments.append({
                    "title": title,
                    "start_date": str(start_d),
                    "end_date": str(end_d),
                    "priority": priority
                })

            # initials
            parts = name.split()
            initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else parts[0][0].upper()

            employees.append({
                "employee_id": employee_id,
                "name": name,
                "initials": initials,
                "role": role,
                "department": dept,
                "experience_years": exp,
                "skills": parsed_skills,
                "availability_status": availability_obj["status"],
                "availability_percent": availability_obj["percent"],
                "active_assignments": assignments
            })

        return {"employees": employees}

    finally:
        cur.close()
        conn.close()
