import pandas as pd
from datetime import datetime

# figures out if someone is busy, partial or available based on project hours
def calculate_availability(row, start=None, end=None):
    # read all the values
    try:
        total_hours = float(row.get("Total Hours", 0))
        remaining_hours = float(row.get("Remaining Hours", 0))
        start_date = pd.to_datetime(row.get("Start Date"), errors="coerce")
        end_date = pd.to_datetime(row.get("End Date"), errors="coerce")
    except Exception:
        return "Available", 100.0  # default if data is messy

    # base calculation
    availability_percent = (remaining_hours / total_hours * 100) if total_hours > 0 else 100

    # optional timeframe filter (for future dashboard)
    if start and end and pd.notna(start_date) and pd.notna(end_date):
        latest_start = max(start_date, start)
        earliest_end = min(end_date, end)
        if latest_start <= earliest_end:
            overlap_days = (earliest_end - latest_start).days + 1
            project_days = (end_date - start_date).days + 1
            if project_days > 0:
                ratio = (remaining_hours / total_hours) * (1 - overlap_days / project_days)
                availability_percent = max(0, min(100, ratio * 100))

    # classify based on percent
    if availability_percent <= 30:
        status = "Busy"
    elif 31 <= availability_percent <= 50:
        status = "Partial"
    else:
        status = "Available"

    return status, round(float(availability_percent), 1)
