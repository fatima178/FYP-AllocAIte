# processing/availability_processing.py

from datetime import date, timedelta
from db import get_connection


def calculate_availability(employee_id: int, window_start: date, window_end: date):
    """
    Calculate availability based on assignments that overlap with the given date window.

    Rules:
    - Total hours = sum of total_hours for overlapping assignments
    - Remaining hours = sum of remaining_hours for overlapping assignments
    - If no overlapping assignments → Available = 100%

    Returns:
        {
            "status": "Available" | "Partial" | "Busy",
            "percent": float
        }
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        # get relevant assignments
        cur.execute("""
            SELECT title, start_date, end_date, total_hours, remaining_hours
            FROM Assignments
            WHERE employee_id = %s
              AND start_date <= %s
              AND end_date >= %s;
        """, (employee_id, window_end, window_start))

        rows = cur.fetchall()

        if not rows:
            # no assignments in this window
            return {"status": "Available", "percent": 100.0}

        total_hours = 0.0
        remaining_hours = 0.0

        for title, start_date, end_date, t_hours, r_hours in rows:
            try:
                t_hours = float(t_hours or 0)
                r_hours = float(r_hours or 0)
            except:
                continue

            total_hours += t_hours
            remaining_hours += r_hours

        if total_hours <= 0:
            return {"status": "Available", "percent": 100.0}

        percent = max(0.0, min(100.0, (remaining_hours / total_hours) * 100))

        if percent <= 30:
            status = "Busy"
        elif 31 <= percent <= 50:
            status = "Partial"
        else:
            status = "Available"

        return {"status": status, "percent": round(percent, 1)}

    finally:
        cur.close()
        conn.close()


def dashboard_window():
    """
    Returns the date window used by the dashboard.
    Next 7 days.
    """
    today = date.today()
    return today, today + timedelta(days=6)
