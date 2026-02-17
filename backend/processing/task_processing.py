from datetime import date, timedelta
from typing import Optional

from db import get_connection


# ----------------------------------------------------------
# custom error for task/assignment-related failures
# ----------------------------------------------------------
# allows raising structured errors that can later be mapped to
# http responses or frontend alerts.
class TaskProcessingError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# ----------------------------------------------------------
# fetch active upload or fall back to latest upload
# ----------------------------------------------------------
# used across all task-related endpoints to know which dataset
# (employees + assignments) should be used.
def _get_active_upload_id(cur, user_id: int) -> Optional[int]:
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

    # fallback to latest upload if no active one exists
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
    return row[0] if row else None


# ----------------------------------------------------------
# normalize a week start date
# ----------------------------------------------------------
# ensures any provided date resolves to the monday of that week.
# if no date provided → default to today's week.
def _normalize_week_start(target: Optional[date]) -> date:
    base = target or date.today()
    return base - timedelta(days=base.weekday())


# ----------------------------------------------------------
# build task payload for weekly timeline display
# ----------------------------------------------------------
# calculates offsets and spans within a 7-day visual grid:
#   - visible_start/end clamp the assignment to the visible calendar window
#   - start_offset is number of days from beginning of week
#   - span is number of visible days the assignment covers
def _build_task_payload(row, week_start: date, week_end: date):
    assignment_id, employee_id, title, start_date, end_date, employee_name = row

    visible_start = max(start_date, week_start)
    visible_end = min(end_date, week_end)

    start_offset = (visible_start - week_start).days
    span = (visible_end - visible_start).days + 1

    return {
        "assignment_id": assignment_id,
        "employee_id": employee_id,
        "employee_name": employee_name or "unassigned",
        "title": title,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "start_offset": start_offset,
        "span": span,
    }


# ----------------------------------------------------------
# fetch weekly tasks for timeline/calendar UI
# ----------------------------------------------------------
# returns:
#   - list of employees and their tasks (grouped per person)
#   - list of unassigned tasks
#   - employee options for dropdown selection
#   - week boundaries (monday to sunday)
def fetch_weekly_tasks(user_id: int, week_start: Optional[date]) -> dict:
    week_start_day = _normalize_week_start(week_start)
    week_end_day = week_start_day + timedelta(days=6)

    conn = get_connection()
    cur = conn.cursor()

    try:
        # fetch employee list for this upload
        cur.execute(
            """
            SELECT employee_id, name
            FROM "Employees"
            WHERE user_id = %s
            ORDER BY name ASC;
            """,
            (user_id,),
        )
        employee_rows = cur.fetchall()

        # fetch all assignments overlapping the requested week
        cur.execute(
            """
            SELECT
                a.assignment_id,
                a.employee_id,
                a.title,
                a.start_date,
                a.end_date,
                e.name
            FROM "Assignments" a
            LEFT JOIN "Employees" e ON a.employee_id = e.employee_id
            WHERE (
              a.user_id = %s
              OR (a.user_id IS NULL AND e.user_id = %s)
            )
              AND a.start_date <= %s
              AND a.end_date >= %s
            ORDER BY e.name NULLS LAST, a.start_date ASC;
            """,
            (user_id, user_id, week_end_day, week_start_day),
        )
        rows = cur.fetchall()

        employees = {}
        unassigned = []

        # group tasks by employee and separate unassigned tasks
        for row in rows:
            payload = _build_task_payload(row, week_start_day, week_end_day)
            emp_id = payload["employee_id"]

            if emp_id is None:
                unassigned.append(payload)
            else:
                if emp_id not in employees:
                    employees[emp_id] = {
                        "employee_id": emp_id,
                        "name": payload["employee_name"],
                        "tasks": [],
                    }
                employees[emp_id]["tasks"].append(payload)

        # sort both groups for consistent ui
        employee_list = list(employees.values())
        employee_list.sort(key=lambda item: item["name"].lower())
        unassigned.sort(key=lambda item: item["title"].lower())

        # build dropdown selection list (includes "unassigned")
        employee_options = [{"employee_id": None, "name": "unassigned"}]
        employee_options.extend(
            {"employee_id": emp_id, "name": name}
            for emp_id, name in employee_rows
        )

        return {
            "week_start": str(week_start_day),
            "week_end": str(week_end_day),
            "employees": employee_list,
            "unassigned": unassigned,
            "employee_options": employee_options,
        }

    except Exception as exc:
        # wrap unexpected errors into structured exception
        raise TaskProcessingError(500, str(exc))

    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------
# create new assignment entry
# ----------------------------------------------------------
# validates:
#   - title present
#   - start <= end
#   - user has active upload
#   - if assigning to employee, validate employee belongs to upload
def create_task_entry(
    user_id: int,
    title: str,
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None,
) -> dict:
    clean_title = (title or "").strip()
    if not clean_title:
        raise TaskProcessingError(400, "title is required")

    if start_date > end_date:
        raise TaskProcessingError(400, "start date cannot be after end date")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # if employee assigned, verify they belong to this dataset
        if employee_id is not None:
            cur.execute(
                """
                SELECT 1
                FROM "Employees"
                WHERE employee_id = %s AND user_id = %s;
                """,
                (employee_id, user_id),
            )
            if not cur.fetchone():
                raise TaskProcessingError(404, "employee not found for this user")

        # insert new assignment
        days = (end_date - start_date).days + 1
        total_hours = float(days * 8)
        cur.execute(
            """
            INSERT INTO "Assignments" (
                user_id,
                employee_id,
                upload_id,
                title,
                start_date,
                end_date,
                total_hours,
                remaining_hours,
                priority
            )
            VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, NULL)
            RETURNING assignment_id;
            """,
            (user_id, employee_id, clean_title, start_date, end_date, total_hours, total_hours),
        )

        assignment_id = cur.fetchone()[0]
        conn.commit()
        return {"assignment_id": assignment_id}

    except TaskProcessingError:
        # expected error →-rethrow after rollback
        conn.rollback()
        raise

    except Exception as exc:
        # unexpected error - wrap into structured exception
        conn.rollback()
        raise TaskProcessingError(500, str(exc))

    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------
# validate assignment ownership
# ----------------------------------------------------------
# ensures the assignment belongs to the user, either via user_id
# or via the linked employee relationship.
def _validate_assignment_owner(cur, assignment_id: int, user_id: int) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM "Assignments" a
        LEFT JOIN "Employees" e ON a.employee_id = e.employee_id
        WHERE a.assignment_id = %s
          AND (
            a.user_id = %s
            OR (a.user_id IS NULL AND e.user_id = %s)
          );
        """,
        (assignment_id, user_id, user_id),
    )
    return bool(cur.fetchone())


# ----------------------------------------------------------
# archive assignment into history before removal
# ----------------------------------------------------------
def _archive_assignment(cur, assignment_id: int):
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
            user_id,
            employee_id,
            upload_id,
            assignment_id,
            title,
            start_date,
            end_date,
            total_hours,
            remaining_hours,
            priority
        FROM "Assignments"
        WHERE assignment_id = %s;
        """,
        (assignment_id,),
    )


# ----------------------------------------------------------
# update assignment entry
# ----------------------------------------------------------
# validates:
#   - title present
#   - start <= end
#   - assignment belongs to user
#   - if employee assigned, validate employee belongs to user
def update_task_entry(
    user_id: int,
    assignment_id: int,
    title: str,
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None,
) -> dict:
    clean_title = (title or "").strip()
    if not clean_title:
        raise TaskProcessingError(400, "title is required")

    if start_date > end_date:
        raise TaskProcessingError(400, "start date cannot be after end date")

    conn = get_connection()
    cur = conn.cursor()

    try:
        if not _validate_assignment_owner(cur, assignment_id, user_id):
            raise TaskProcessingError(404, "task not found for this user")

        # if employee assigned, verify they belong to this user
        if employee_id is not None:
            cur.execute(
                """
                SELECT 1
                FROM "Employees"
                WHERE employee_id = %s AND user_id = %s;
                """,
                (employee_id, user_id),
            )
            if not cur.fetchone():
                raise TaskProcessingError(404, "employee not found for this user")

        # preserve existing hours unless missing
        cur.execute(
            """
            SELECT total_hours, remaining_hours
            FROM "Assignments"
            WHERE assignment_id = %s;
            """,
            (assignment_id,),
        )
        row = cur.fetchone()
        total_hours = row[0] if row else None
        remaining_hours = row[1] if row else None

        if total_hours is None:
            days = (end_date - start_date).days + 1
            total_hours = float(days * 8)
        if remaining_hours is None:
            remaining_hours = total_hours

        cur.execute(
            """
            UPDATE "Assignments"
            SET title = %s,
                start_date = %s,
                end_date = %s,
                employee_id = %s,
                user_id = %s,
                total_hours = %s,
                remaining_hours = %s
            WHERE assignment_id = %s;
            """,
            (
                clean_title,
                start_date,
                end_date,
                employee_id,
                user_id,
                total_hours,
                remaining_hours,
                assignment_id,
            ),
        )

        conn.commit()
        return {"assignment_id": assignment_id}

    except TaskProcessingError:
        conn.rollback()
        raise

    except Exception as exc:
        conn.rollback()
        raise TaskProcessingError(500, str(exc))

    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------
# delete assignment entry
# ----------------------------------------------------------
# validates:
#   - assignment belongs to user
def delete_task_entry(user_id: int, assignment_id: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()

    try:
        if not _validate_assignment_owner(cur, assignment_id, user_id):
            raise TaskProcessingError(404, "task not found for this user")

        _archive_assignment(cur, assignment_id)

        cur.execute(
            """
            DELETE FROM "Assignments"
            WHERE assignment_id = %s;
            """,
            (assignment_id,),
        )

        conn.commit()
        return {"message": "Task deleted"}

    except TaskProcessingError:
        conn.rollback()
        raise

    except Exception as exc:
        conn.rollback()
        raise TaskProcessingError(500, str(exc))

    finally:
        cur.close()
        conn.close()
