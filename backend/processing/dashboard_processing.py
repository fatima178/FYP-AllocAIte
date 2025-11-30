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
        select upload_id
        from uploads
        where user_id = %s and is_active = true
        order by upload_date desc
        limit 1;
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
        upload_id = get_latest_upload_id(cur, user_id)

        # if user hasn't uploaded anything yet, return empty numbers
        if not upload_id:
            return {
                "total_employees": 0,
                "active_projects": 0,
                "available_next_7_days": 0,
                "available_this_week": 0,
            }

        # 1. total employees tied to this upload
        cur.execute("""
            select count(*) 
            from employees 
            where upload_id = %s;
        """, (upload_id,))
        total_employees = cur.fetchone()[0]

        # 2. active projects: assignments overlapping today's date
        today = date.today()
        cur.execute("""
            select count(*)
            from assignments
            where upload_id = %s
              and start_date <= %s
              and end_date >= %s;
        """, (upload_id, today, today))
        active_projects = cur.fetchone()[0]

        # 3. employees available in the next 7 days
        window_start, window_end = dashboard_window()

        cur.execute("""
            select employee_id
            from employees
            where upload_id = %s;
        """, (upload_id,))
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
        upload_id = get_latest_upload_id(cur, user_id)
        if not upload_id:
            # user has no upload → dashboard shows empty list
            return {"employees": []}

        window_start, window_end = dashboard_window()

        # fetch full employee records
        cur.execute("""
            select employee_id, name, role, department, experience_years, skills
            from employees
            where upload_id = %s
            order by name asc;
        """, (upload_id,))
        rows = cur.fetchall()

        employees = []

        for emp in rows:
            employee_id, name, role, dept, exp, skills_json = emp

       
            # parse skills (stored as json array or string)
            parsed_skills = []
            if isinstance(skills_json, list):
                parsed_skills = skills_json
            elif isinstance(skills_json, str):
                try:
                    import json
                    parsed_skills = json.loads(skills_json)
                except:
                    parsed_skills = []

            # search filter (matches name or role)
            if search:
                st = search.lower()
                if st not in name.lower() and st not in role.lower():
                    continue


            # skills filter
            # requires that the employee has all skills in the filter list
            if skills:
                lower_emp = [s.lower() for s in parsed_skills]
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

            # fetch assignments active today
            today = date.today()
            cur.execute("""
                select title, start_date, end_date, priority
                from assignments
                where employee_id = %s
                  and start_date <= %s
                  and end_date >= %s;
            """, (employee_id, today, today))

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
