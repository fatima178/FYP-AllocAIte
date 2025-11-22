from datetime import date
from typing import Optional

from db import get_connection


def _resolve_upload_id(cur, user_id: int, requested_upload_id: Optional[int] = None):
    if requested_upload_id is not None:
        cur.execute(
            """
            SELECT upload_id
            FROM uploads
            WHERE upload_id = %s AND user_id = %s
            LIMIT 1;
            """,
            (requested_upload_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Upload not found for this user.")
        return row[0]

    cur.execute(
        """
        SELECT upload_id
        FROM uploads
        WHERE user_id = %s AND is_active = TRUE
        ORDER BY upload_date DESC
        LIMIT 1;
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        """
        SELECT upload_id
        FROM uploads
        WHERE user_id = %s
        ORDER BY upload_date DESC
        LIMIT 1;
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    raise ValueError("No uploads found for this user.")


def assign_recommended_task(
    user_id: int,
    employee_id: int,
    title: str,
    start_date: str,
    end_date: str,
    upload_id: Optional[int] = None,
):
    clean_title = (title or "").strip()
    if not clean_title:
        raise ValueError("Task description is required.")

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise ValueError("Invalid start or end date.")

    if start > end:
        raise ValueError("Start date cannot be after end date.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        resolved_upload_id = _resolve_upload_id(cur, user_id, upload_id)

        cur.execute(
            """
            SELECT 1
            FROM employees
            WHERE employee_id = %s AND upload_id = %s;
            """,
            (employee_id, resolved_upload_id),
        )
        if not cur.fetchone():
            raise ValueError("Employee not found for this upload.")

        cur.execute(
            """
            INSERT INTO assignments (
                employee_id,
                upload_id,
                title,
                start_date,
                end_date,
                total_hours,
                remaining_hours,
                priority
            )
            VALUES (%s, %s, %s, %s, %s, NULL, NULL, NULL)
            RETURNING assignment_id;
            """,
            (
                employee_id,
                resolved_upload_id,
                clean_title,
                start,
                end,
            ),
        )

        assignment_id = cur.fetchone()[0]
        conn.commit()
        return {
            "assignment_id": assignment_id,
            "employee_id": employee_id,
            "title": clean_title,
            "start_date": str(start),
            "end_date": str(end),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
