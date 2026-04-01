from datetime import date, timedelta
from db import get_connection


# ----------------------------------------------------------
# calculate availability for a given employee within a date window
# ----------------------------------------------------------
# logic:
#   - find all assignments that overlap with the query window
#   - accumulate total hours and remaining hours across those assignments
#   - availability % = (remaining_hours / total_hours) * 100
#   - if no overlapping assignments → full availability
#   - availability bands:
#         > 50% remaining  → "available"
#         31–50% remaining → "partial"
#         ≤ 30% remaining  → "busy"
def calculate_availability_from_rows(rows, window_start: date, window_end: date):
    if not rows:
        return {"status": "Available", "percent": 100.0}

    remaining_hours = 0.0

    for _, start_date, end_date, t_hours, r_hours in rows:
        try:
            t_hours = float(t_hours or 0)
        except Exception:
            t_hours = 0
        try:
            r_hours = float(r_hours or 0)
        except Exception:
            r_hours = 0

        assignment_days = (end_date - start_date).days + 1
        window_days = (min(end_date, window_end) - max(start_date, window_start)).days + 1
        if assignment_days <= 0 or window_days <= 0:
            continue

        base_hours = r_hours if r_hours > 0 else t_hours
        if base_hours <= 0:
            base_hours = float(assignment_days * 8)

        hours_per_day = base_hours / assignment_days
        remaining_hours += hours_per_day * window_days

    window_capacity = float((window_end - window_start).days + 1) * 8
    if window_capacity <= 0:
        return {"status": "Busy", "percent": 0.0}

    percent = max(0.0, min(100.0, (1 - (remaining_hours / window_capacity)) * 100))

    if percent <= 30:
        status = "Busy"
    elif 31 <= percent <= 50:
        status = "Partial"
    else:
        status = "Available"

    return {"status": status, "percent": round(percent, 1)}


def calculate_availability(employee_id: int, window_start: date, window_end: date):
    """
    computes availability based on assignments overlapping the given date window.
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT title, start_date, end_date, total_hours, remaining_hours
            FROM "Assignments"
            WHERE employee_id = %s
              AND start_date <= %s
              AND end_date >= %s;
        """, (employee_id, window_end, window_start))
        rows = cur.fetchall()
        return calculate_availability_from_rows(rows, window_start, window_end)
    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------
# dashboard window helper
# ----------------------------------------------------------
# returns a fixed 7-day window (today → +6 days)
# used by dashboards to show upcoming availability
def dashboard_window():
    today = date.today()
    return today, today + timedelta(days=6)
