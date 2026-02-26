from datetime import date, timedelta
from typing import Optional

from db import get_connection
from processing.employee_profile_processing import _resolve_employee_id, EmployeeProfileError


class EmployeeCalendarError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _normalize_week_start(target: Optional[date]) -> date:
    base = target or date.today()
    return base - timedelta(days=base.weekday())


def _build_item_payload(title: str, start_date: date, end_date: date, week_start: date, week_end: date, kind: str, item_id: int):
    visible_start = max(start_date, week_start)
    visible_end = min(end_date, week_end)
    start_offset = (visible_start - week_start).days
    span = (visible_end - visible_start).days + 1
    return {
        "id": item_id,
        "type": kind,
        "title": title,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "start_offset": start_offset,
        "span": span,
    }


def fetch_employee_calendar(user_id: int, week_start: Optional[date]) -> dict:
    employee_id = _resolve_employee_id(user_id)
    week_start_day = _normalize_week_start(week_start)
    week_end_day = week_start_day + timedelta(days=6)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT name
            FROM "Employees"
            WHERE employee_id = %s;
            """,
            (employee_id,),
        )
        row = cur.fetchone()
        if not row:
            raise EmployeeCalendarError(404, "employee not found")
        employee_name = row[0]

        cur.execute(
            """
            SELECT assignment_id, title, start_date, end_date
            FROM "Assignments"
            WHERE employee_id = %s
              AND start_date <= %s
              AND end_date >= %s
            ORDER BY start_date ASC;
            """,
            (employee_id, week_end_day, week_start_day),
        )
        assignment_rows = cur.fetchall()

        cur.execute(
            """
            SELECT entry_id, label, start_date, end_date
            FROM "EmployeeCalendarEntries"
            WHERE employee_id = %s
              AND start_date <= %s
              AND end_date >= %s
            ORDER BY start_date ASC;
            """,
            (employee_id, week_end_day, week_start_day),
        )
        personal_rows = cur.fetchall()

        items = [
            _build_item_payload(title, start_date, end_date, week_start_day, week_end_day, "assignment", assignment_id)
            for assignment_id, title, start_date, end_date in assignment_rows
        ]

        for entry_id, label, start_date, end_date in personal_rows:
            items.append(
                _build_item_payload(
                    label,
                    start_date,
                    end_date,
                    week_start_day,
                    week_end_day,
                    "personal",
                    entry_id,
                )
            )

        items.sort(key=lambda item: (item["start_date"], item["title"].lower()))

        return {
            "week_start": str(week_start_day),
            "week_end": str(week_end_day),
            "employee": {"employee_id": employee_id, "name": employee_name},
            "items": items,
        }
    except EmployeeProfileError as exc:
        raise EmployeeCalendarError(exc.status_code, exc.message)
    except EmployeeCalendarError:
        raise
    except Exception as exc:
        raise EmployeeCalendarError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def create_personal_calendar_entry(user_id: int, label: str, start_date: date, end_date: date) -> dict:
    employee_id = _resolve_employee_id(user_id)
    clean_label = str(label or "").strip()
    if not clean_label:
        raise EmployeeCalendarError(400, "label is required")
    if start_date > end_date:
        raise EmployeeCalendarError(400, "start_date cannot be after end_date")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO "EmployeeCalendarEntries" (employee_id, label, start_date, end_date)
            VALUES (%s, %s, %s, %s)
            RETURNING entry_id;
            """,
            (employee_id, clean_label, start_date, end_date),
        )
        entry_id = cur.fetchone()[0]
        conn.commit()
        return {"entry_id": entry_id}
    except Exception as exc:
        conn.rollback()
        raise EmployeeCalendarError(500, str(exc))
    finally:
        cur.close()
        conn.close()
