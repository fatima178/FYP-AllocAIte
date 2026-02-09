# processing/dashboard_processing.py

from datetime import date
from db import get_connection
from processing.availability_processing import calculate_availability, dashboard_window


# ----------------------------------------------------------
# get the latest active upload for a user
# ----------------------------------------------------------
# this determines which dataset the dashboard should use.
# if no active upload exists, returns none.
def get_latest_upload_id(cur, user_id: int):
    cur.execute("""
        SELECT upload_id
        FROM "Uploads"
        WHERE user_id = %s AND is_active = TRUE
        ORDER BY upload_date DESC
        LIMIT 1;
    """, (user_id,))
    result = cur.fetchone()
    return result[0] if result else None


# ----------------------------------------------------------
# compute dashboard wide summary stats
# ----------------------------------------------------------
# this builds the main numbers shown at the top of the dashboard:
#   - total employees
#   - active projects (assignments running today)
#   - employees available in next 7 days
#   - available_this_week mirrors this for frontend consistency
def get_dashboard_summary(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM "Employees"
            WHERE user_id = %s;
        """, (user_id,))
        total_employees = cur.fetchone()[0]

        # if user hasn't uploaded anything yet, return empty numbers
        if total_employees == 0:
            return {
                "total_employees": 0,
                "active_projects": 0,
                "available_next_7_days": 0,
                "available_this_week": 0,
            }

        # 2. active projects: assignments overlapping today's date
        today = date.today()
        cur.execute("""
            SELECT COUNT(*)
            FROM "Assignments" a
            JOIN "Employees" e ON a.employee_id = e.employee_id
            WHERE e.user_id = %s
              AND a.start_date <= %s
              AND a.end_date >= %s;
        """, (user_id, today, today))
        active_projects = cur.fetchone()[0]

        # 3. employees available in the next 7 days
        window_start, window_end = dashboard_window()

        cur.execute("""
            SELECT employee_id
            FROM "Employees"
            WHERE user_id = %s;
        """, (user_id,))
        employees = cur.fetchall()

        available_count = 0
        for (employee_id,) in employees:
            result = calculate_availability(employee_id, window_start, window_end)

            # only count fully available employees
            if result["status"].lower() == "available":
                available_count += 1

        # compile summary into a consistent structure
        summary = {
            "total_employees": total_employees,
            "active_projects": active_projects,
            "available_next_7_days": available_count,
        }

        # available_this_week is same as 7-day window
        summary["available_this_week"] = summary["available_next_7_days"]

        return summary

    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------
# fetch all employee data for dashboard listing
# ----------------------------------------------------------
# this returns:
#   - employee core info
#   - parsed skills
#   - dynamic availability (7-day window)
#   - active assignments happening today
# supports filtering by:
#   - search text (name or role)
#   - required skills
#   - availability level
def get_employees_data(user_id: int, search=None, skills=None, availability=None):

    # returns a structured list of employees + availability + active assignments.

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM "Employees"
            WHERE user_id = %s;
        """, (user_id,))
        if cur.fetchone()[0] == 0:
            return {"employees": []}

        window_start, window_end = dashboard_window()

        # fetch full employee records
        cur.execute("""
            SELECT employee_id, name, role, department
            FROM "Employees"
            WHERE user_id = %s
            ORDER BY name ASC;
        """, (user_id,))
        rows = cur.fetchall()

        employees = []

        for emp in rows:
            employee_id, name, role, dept = emp

            cur.execute("""
                SELECT skill_name, years_experience
                FROM "EmployeeSkills"
                WHERE employee_id = %s
                ORDER BY skill_name ASC;
            """, (employee_id,))
            parsed_skills = [
                {"skill_name": s, "years_experience": y}
                for s, y in cur.fetchall()
            ]

            # search filter (matches name or role)
            if search:
                st = search.lower()
                if st not in name.lower() and st not in role.lower():
                    continue


            # skills filter
            # requires that the employee has all skills in the filter list
            if skills:
                lower_emp = [s["skill_name"].lower() for s in parsed_skills]
                lower_filt = [s.lower() for s in skills]
                if not all(s in lower_emp for s in lower_filt):
                    continue

            # compute availability for next 7 days
            availability_obj = calculate_availability(
                employee_id, window_start, window_end
            )

            # availability filter (exact match)
            if availability:
                if availability_obj["status"].lower() != availability.lower():
                    continue

            # fetch assignments active in the dashboard window
            cur.execute("""
                SELECT title, start_date, end_date, priority
                FROM "Assignments"
                WHERE employee_id = %s
                  AND start_date <= %s
                  AND end_date >= %s;
            """, (employee_id, window_end, window_start))

            assignments = []
            for title, start_d, end_d, priority in cur.fetchall():
                assignments.append({
                    "title": title,
                    "start_date": str(start_d),
                    "end_date": str(end_d),
                    "priority": priority
                })

            # generate initials for UI
            parts = name.split()
            initials = (
                parts[0][0] + parts[-1][0]
            ).upper() if len(parts) >= 2 else parts[0][0].upper()

            # final employee object pushed to the result list
            employees.append({
                "employee_id": employee_id,
                "name": name,
                "initials": initials,
                "role": role,
                "department": dept,
                "skills": parsed_skills,
                "availability_status": availability_obj["status"],
                "availability_percent": availability_obj["percent"],
                "active_assignments": assignments
            })

        return {"employees": employees}

    finally:
        cur.close()
        conn.close()
