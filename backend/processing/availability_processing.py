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
def calculate_availability(employee_id: int, window_start: date, window_end: date):
    """
    computes availability based on assignments overlapping the given date window.
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        # fetch any assignments that overlap with the requested window
        # overlap rule: assignment.start <= window_end AND assignment.end >= window_start
        cur.execute("""
            SELECT title, start_date, end_date, total_hours, remaining_hours
            FROM "Assignments"
            WHERE employee_id = %s
              AND start_date <= %s
              AND end_date >= %s;
        """, (employee_id, window_end, window_start))

        rows = cur.fetchall()

        # no assignments means fully available
        if not rows:
            return {"status": "Available", "percent": 100.0}

        total_hours = 0.0
        remaining_hours = 0.0

        # accumulate hours across all overlapping assignments
        for title, start_date, end_date, t_hours, r_hours in rows:
            try:
                t_hours = float(t_hours or 0)
                r_hours = float(r_hours or 0)
            except:
                # skip rows with invalid numeric fields
                continue

            total_hours += t_hours
            remaining_hours += r_hours

        # if total hours somehow equal zero, assume full availability
        if total_hours <= 0:
            return {"status": "Available", "percent": 100.0}

        # compute remaining capacity as percentage
        percent = max(0.0, min(100.0, (remaining_hours / total_hours) * 100))

        # determine availability label
        if percent <= 30:
            status = "Busy"
        elif 31 <= percent <= 50:
            status = "Partial"
        else:
            status = "Available"

        return {"status": status, "percent": round(percent, 1)}

    finally:
        # always close db resources even if an error happens
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
