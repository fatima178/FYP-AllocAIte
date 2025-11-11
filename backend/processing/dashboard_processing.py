from db import get_connection
from datetime import date

def get_dashboard_summary():
    conn = get_connection()
    cur = conn.cursor()

    try:
        # get the latest active upload (so only show data for the newest file)
        cur.execute("SELECT upload_id FROM uploads WHERE is_active = TRUE ORDER BY upload_date DESC LIMIT 1;")
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
            SELECT COUNT(DISTINCT current_project)
            FROM employees
            WHERE upload_id = %s
              AND current_project IS NOT NULL
              AND current_project <> ''
              AND start_date <= %s
              AND end_date >= %s;
        """, (upload_id, today, today))
        active_projects = cur.fetchone()[0] or 0

        # count how many employees are marked as available
        cur.execute("""
            SELECT COUNT(DISTINCT name)
            FROM employees
            WHERE upload_id = %s AND LOWER(availability_status) = 'available';
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
