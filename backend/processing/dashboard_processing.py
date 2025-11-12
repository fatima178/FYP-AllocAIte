from db import get_connection
from datetime import date
import json


def get_dashboard_summary():
    conn = get_connection()
    cur = conn.cursor()

    try:
        # get the latest active upload
        cur.execute("""
            SELECT upload_id
            FROM uploads
            WHERE is_active = TRUE
            ORDER BY upload_date DESC
            LIMIT 1;
        """)
        result = cur.fetchone()
        if not result:
            return {
                "total_employees": 0,
                "active_projects": 0,
                "available_this_week": 0
            }

        upload_id = result[0]
        today = date.today()

        # count how many unique employees are in the current upload
        cur.execute("""
            SELECT COUNT(DISTINCT name)
            FROM employees
            WHERE upload_id = %s;
        """, (upload_id,))
        total_employees = cur.fetchone()[0] or 0

        # count how many unique projects are still active (based on start and end date)
        cur.execute("""
            SELECT COUNT(DISTINCT elem->>'title')
            FROM employees,
                 jsonb_array_elements(active_assignments) AS elem
            WHERE upload_id = %s
              AND elem->>'start_date' IS NOT NULL
              AND elem->>'end_date' IS NOT NULL
              AND elem->>'start_date' NOT IN ('', 'NaT')
              AND elem->>'end_date' NOT IN ('', 'NaT')
              AND (elem->>'start_date')::date <= CURRENT_DATE
              AND (elem->>'end_date')::date >= CURRENT_DATE;
        """, (upload_id,))
        active_projects = cur.fetchone()[0] or 0

        # count how many employees are marked as available
        cur.execute("""
            SELECT COUNT(DISTINCT name)
            FROM employees
            WHERE upload_id = %s
              AND LOWER(availability_status) = 'available';
        """, (upload_id,))
        available_this_week = cur.fetchone()[0] or 0

        # return everything as one summary dictionary for the dashboard
        return {
            "total_employees": total_employees,
            "active_projects": active_projects,
            "available_this_week": available_this_week
        }

    finally:
        # close the database connection so nothing stays open
        cur.close()
        conn.close()


def get_employees_data():
    conn = get_connection()
    cur = conn.cursor()

    try:
        # get the latest active upload
        cur.execute("""
            SELECT upload_id
            FROM uploads
            WHERE is_active = TRUE
            ORDER BY upload_date DESC
            LIMIT 1;
        """)
        result = cur.fetchone()
        if not result:
            return {"employees": []}

        upload_id = result[0]

        # fetch all employees for that upload
        cur.execute("""
            SELECT 
                employee_id,
                name,
                role,
                department,
                experience_years,
                skills,
                availability_status,
                active_assignments
            FROM employees
            WHERE upload_id = %s
            ORDER BY name ASC;
        """, (upload_id,))

        rows = cur.fetchall()

        def parse_json_field(value, default):
            if isinstance(value, (list, dict)):
                return value
            if isinstance(value, str) and value.strip():
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return default
            return default

        employees = []
        for r in rows:
            name = r[1] or ""
            # create initials (first and last letter of full name)
            parts = name.split()
            initials = ""
            if len(parts) >= 2:
                initials = parts[0][0] + parts[-1][0]
            elif len(parts) == 1:
                initials = parts[0][0]
            initials = initials.upper()

            skills = [s.strip() for s in parse_json_field(r[5], []) if s.strip()]
            assignments = [
                a for a in parse_json_field(r[7], [])
                if a.get("title") and a["title"] not in ["—", "-", "None", "NaN", ""]
                and a.get("start_date") and a.get("end_date")
            ]

            employees.append({
                "employee_id": r[0],
                "name": name,
                "initials": initials,
                "role": r[2],
                "department": r[3],
                "experience_years": r[4],
                "skills": skills,
                "availability_status": r[6],
                "active_assignments": assignments
            })

        return {"employees": employees}

    finally:
        cur.close()
        conn.close()
