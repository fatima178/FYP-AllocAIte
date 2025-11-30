from datetime import date
from typing import Optional

from db import get_connection


# ----------------------------------------------------------
# resolve which upload_id to use
# ----------------------------------------------------------
# this function determines which dataset an operation should apply to.
# priority:
#   1) if caller explicitly provides upload_id → validate it belongs to user
#   2) use most recent active upload
#   3) fallback to most recent upload ever uploaded by this user
def _resolve_upload_id(cur, user_id: int, requested_upload_id: Optional[int] = None):
    # caller explicitly requested an upload id, validate it
    if requested_upload_id is not None:
        cur.execute(
            """
            SELECT upload_id
            FROM "Uploads"
            WHERE upload_id = %s AND user_id = %s
            LIMIT 1;
            """,
            (requested_upload_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("upload not found for this user.")
        return row[0]

    # else: automatically select user's latest active upload
    cur.execute(
        """
        SELECT upload_id
        FROM "Uploads"
        WHERE user_id = %s AND is_active = TRUE
        ORDER BY upload_date DESC
        LIMIT 1;
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # fallback: use most recent upload even if it's inactive
    cur.execute(
        """
        SELECT upload_id
        FROM "Uploads"
        WHERE user_id = %s
        ORDER BY upload_date DESC
        LIMIT 1;
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # no uploads at all for this user
    raise ValueError("no uploads found for this user.")


# ----------------------------------------------------------
# assign a recommended task to an employee
# ----------------------------------------------------------
# validates:
#   - title is not empty
#   - dates are valid iso strings
#   - start <= end
#   - employee belongs to the resolved upload dataset
#
# inserts the assignment into the assignments table and returns metadata.
def assign_recommended_task(
    user_id: int,
    employee_id: int,
    title: str,
    start_date: str,
    end_date: str,
    upload_id: Optional[int] = None,
):
    # clean task title
    clean_title = (title or "").strip()
    if not clean_title:
        raise ValueError("task description is required.")

    # validate date format (must be yyyy-mm-dd)
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise ValueError("invalid start or end date.")

    # ensure the time interval is logically valid
    if start > end:
        raise ValueError("start date cannot be after end date.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # determine which upload_id the assignment should attach to
        resolved_upload_id = _resolve_upload_id(cur, user_id, upload_id)

        # ensure employee exists within this upload dataset
        cur.execute(
            """
            SELECT 1
            FROM "Employees"
            WHERE employee_id = %s AND upload_id = %s;
            """,
            (employee_id, resolved_upload_id),
        )
        if not cur.fetchone():
            raise ValueError("employee not found for this upload.")

        # insert assignment into database
        # total_hours, remaining_hours, priority are left null, to be filled later
        cur.execute(
            """
            INSERT INTO "Assignments" (
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

        # return structured result for frontend
        return {
            "assignment_id": assignment_id,
            "employee_id": employee_id,
            "title": clean_title,
            "start_date": str(start),
            "end_date": str(end),
        }

    except Exception:
        # rollback safe in case anything goes wrong mid insert
        conn.rollback()
        raise

    finally:
        # always close db resources
        cur.close()
        conn.close()
