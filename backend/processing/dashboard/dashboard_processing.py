from db import get_connection
from processing.availability_processing import calculate_availability_from_rows, dashboard_window
from processing.assignment_history_processing import archive_completed_assignments


def _merge_skills(skill_rows):
    merged = {}
    for employee_id, skill_name, years_experience, skill_type in skill_rows:
        if skill_type != "technical":
            continue
        label = str(skill_name or "").strip()
        if not label:
            continue
        key = (employee_id, label.lower())
        if key not in merged:
            merged[key] = {"skill_name": label, "years_experience": years_experience}
            continue
        try:
            merged[key]["years_experience"] = max(
                merged[key].get("years_experience") or 0,
                years_experience or 0,
            )
        except Exception:
            merged[key]["years_experience"] = merged[key].get("years_experience") or years_experience
    return merged


# ----------------------------------------------------------
# compute dashboard wide summary stats
# ----------------------------------------------------------
# this builds the main numbers shown at the top of the dashboard:
#   - total employees
#   - active projects (assignments running today)
#   - employees available in next 7 days
#   - available_this_week mirrors this for frontend consistency
def get_dashboard_summary(user_id: int, window_start=None, window_end=None):
    conn = get_connection()
    cur = conn.cursor()

    try:
        archive_completed_assignments(user_id)

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

        if not window_start or not window_end:
            window_start, window_end = dashboard_window()

        # active projects: assignments overlapping the selected window
        cur.execute("""
            SELECT COUNT(*)
            FROM "Assignments" a
            JOIN "Employees" e ON a.employee_id = e.employee_id
            WHERE e.user_id = %s
              AND a.start_date <= %s
              AND a.end_date >= %s;
        """, (user_id, window_end, window_start))
        active_projects = cur.fetchone()[0]

        # 3. employees available in the next 7 days
        cur.execute("""
            SELECT employee_id
            FROM "Employees"
            WHERE user_id = %s;
        """, (user_id,))
        employees = cur.fetchall()

        employee_ids = [employee_id for (employee_id,) in employees]
        assignment_map = {employee_id: [] for employee_id in employee_ids}
        if employee_ids:
            cur.execute(
                """
                SELECT employee_id, title, start_date, end_date, total_hours, remaining_hours
                FROM "Assignments"
                WHERE employee_id = ANY(%s)
                  AND start_date <= %s
                  AND end_date >= %s;
                """,
                (employee_ids, window_end, window_start),
            )
            for row in cur.fetchall():
                assignment_map.setdefault(row[0], []).append(row[1:])

        available_count = 0
        for employee_id in employee_ids:
            result = calculate_availability_from_rows(
                assignment_map.get(employee_id, []),
                window_start,
                window_end,
            )
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
def get_employees_data(
    user_id: int,
    search=None,
    skills=None,
    availability=None,
    window_start=None,
    window_end=None,
):

    # returns a structured list of employees + availability + active assignments.

    conn = get_connection()
    cur = conn.cursor()

    try:
        archive_completed_assignments(user_id)

        cur.execute("""
            SELECT COUNT(*)
            FROM "Employees"
            WHERE user_id = %s;
        """, (user_id,))
        if cur.fetchone()[0] == 0:
            return {"employees": []}

        if not window_start or not window_end:
            window_start, window_end = dashboard_window()

        cur.execute("""
            SELECT employee_id, name, role, department
            FROM "Employees"
            WHERE user_id = %s
            ORDER BY name ASC;
        """, (user_id,))
        rows = cur.fetchall()

        employee_ids = [employee_id for employee_id, _, _, _ in rows]
        employees = []
        skill_map = {employee_id: [] for employee_id in employee_ids}
        soft_skill_map = {employee_id: [] for employee_id in employee_ids}
        assignment_map = {employee_id: [] for employee_id in employee_ids}
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
            merged_skills = _merge_skills(cur.fetchall())
            for (employee_id, _), skill_payload in merged_skills.items():
                skill_map.setdefault(employee_id, []).append(skill_payload)

            cur.execute(
                """
                SELECT employee_id, skill_name, years_experience
                FROM "EmployeeSkills"
                WHERE employee_id = ANY(%s)
                  AND skill_type = 'soft'
                ORDER BY employee_id ASC, skill_name ASC;
                """,
                (employee_ids,),
            )
            for employee_id, skill_name, years_experience in cur.fetchall():
                soft_skill_map.setdefault(employee_id, []).append(
                    {"skill_name": skill_name, "years_experience": years_experience}
                )

            cur.execute(
                """
                SELECT employee_id, title, start_date, end_date, total_hours, remaining_hours
                FROM "Assignments"
                WHERE employee_id = ANY(%s)
                  AND start_date <= %s
                  AND end_date >= %s
                ORDER BY employee_id ASC, start_date ASC;
                """,
                (employee_ids, window_end, window_start),
            )
            for employee_id, title, start_date, end_date, total_hours, remaining_hours in cur.fetchall():
                assignment_map.setdefault(employee_id, []).append(
                    (title, start_date, end_date, total_hours, remaining_hours)
                )


        for employee_id, name, role, dept in rows:
            parsed_skills = skill_map.get(employee_id, [])
            soft_skills = soft_skill_map.get(employee_id, [])

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
            availability_obj = calculate_availability_from_rows(
                assignment_map.get(employee_id, []),
                window_start,
                window_end,
            )

            # availability filter (exact match)
            if availability:
                if availability_obj["status"].lower() != availability.lower():
                    continue

            # fetch assignments active in the dashboard window
            assignments = []
            for title, start_d, end_d, _, _ in assignment_map.get(employee_id, []):
                assignments.append({
                    "title": title,
                    "start_date": str(start_d),
                    "end_date": str(end_d),
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
                "soft_skills": soft_skills,
                "availability_status": availability_obj["status"],
                "availability_percent": availability_obj["percent"],
                "active_assignments": assignments
            })

        return {"employees": employees}

    finally:
        cur.close()
        conn.close()
