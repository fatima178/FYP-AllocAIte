from datetime import date
from typing import Optional

from db import get_connection


# custom error so routes can return a clear status/message if archiving fails
class AssignmentHistoryError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def archive_completed_assignments(user_id: int, as_of: Optional[date] = None) -> int:
    # default to today's date, but allow tests/manual calls to pass another date
    cutoff = as_of or date.today()

    conn = get_connection()
    cur = conn.cursor()
    try:
        # copy finished assignments into history first
        # NOT EXISTS prevents the same assignment being archived more than once
        cur.execute(
            """
            INSERT INTO "AssignmentHistory" (
                user_id,
                employee_id,
                upload_id,
                source_assignment_id,
                title,
                start_date,
                end_date,
                total_hours,
                remaining_hours
            )
            SELECT
                a.user_id,
                a.employee_id,
                a.upload_id,
                a.assignment_id,
                a.title,
                a.start_date,
                a.end_date,
                a.total_hours,
                a.remaining_hours
            FROM "Assignments" a
            LEFT JOIN "Employees" e ON a.employee_id = e.employee_id
            WHERE (
                a.user_id = %s
                OR (a.user_id IS NULL AND e.user_id = %s)
            )
              AND a.end_date < %s
              AND NOT EXISTS (
                SELECT 1
                FROM "AssignmentHistory" h
                WHERE h.source_assignment_id = a.assignment_id
              );
            """,
            (user_id, user_id, cutoff),
        )

        # after the history row exists, remove the old active assignment
        # this keeps dashboards focused on current/upcoming work
        cur.execute(
            """
            DELETE FROM "Assignments" a
            USING "Employees" e
            WHERE a.employee_id = e.employee_id
              AND (
                a.user_id = %s
                OR (a.user_id IS NULL AND e.user_id = %s)
              )
              AND a.end_date < %s
              AND EXISTS (
                SELECT 1
                FROM "AssignmentHistory" h
                WHERE h.source_assignment_id = a.assignment_id
              );
            """,
            (user_id, user_id, cutoff),
        )

        # rowcount here is the number of assignments removed from active assignments
        archived = cur.rowcount
        conn.commit()
        return archived

    except Exception as exc:
        conn.rollback()
        raise AssignmentHistoryError(500, str(exc))
    finally:
        cur.close()
        conn.close()
