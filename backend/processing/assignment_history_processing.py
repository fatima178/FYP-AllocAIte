from datetime import date
from typing import Optional

from db import get_connection


class AssignmentHistoryError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def archive_completed_assignments(user_id: int, as_of: Optional[date] = None) -> int:
    cutoff = as_of or date.today()

    conn = get_connection()
    cur = conn.cursor()
    try:
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
                remaining_hours,
                priority
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
                a.remaining_hours,
                a.priority
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

        archived = cur.rowcount
        conn.commit()
        return archived

    except Exception as exc:
        conn.rollback()
        raise AssignmentHistoryError(500, str(exc))
    finally:
        cur.close()
        conn.close()
