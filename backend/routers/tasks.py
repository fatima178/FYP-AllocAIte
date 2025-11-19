from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from db import get_connection

router = APIRouter()


class TaskCreate(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1)
    start_date: date
    end_date: date
    employee_id: Optional[int] = None


def get_active_upload_id(cur, user_id: int) -> Optional[int]:
    cur.execute("""
        SELECT upload_id
        FROM Uploads
        WHERE user_id = %s AND is_active = TRUE
        ORDER BY upload_date DESC
        LIMIT 1;
    """, (user_id,))
    row = cur.fetchone()
    return row[0] if row else None


def normalize_week_start(target: Optional[date]) -> date:
    base = target or date.today()
    return base - timedelta(days=base.weekday())


def build_task_payload(row, week_start: date, week_end: date):
    assignment_id, employee_id, title, start_date, end_date, employee_name = row

    visible_start = max(start_date, week_start)
    visible_end = min(end_date, week_end)
    start_offset = (visible_start - week_start).days
    span = (visible_end - visible_start).days + 1

    return {
        "assignment_id": assignment_id,
        "employee_id": employee_id,
        "employee_name": employee_name or "Unassigned",
        "title": title,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "start_offset": start_offset,
        "span": span,
    }


@router.get("/tasks/week")
def get_weekly_tasks(user_id: int, week_start: Optional[date] = Query(None)):
    week_start_day = normalize_week_start(week_start)
    week_end_day = week_start_day + timedelta(days=6)

    conn = get_connection()
    cur = conn.cursor()

    try:
        upload_id = get_active_upload_id(cur, user_id)
        if not upload_id:
            return {
                "week_start": str(week_start_day),
                "week_end": str(week_end_day),
                "employees": [],
                "unassigned": [],
                "employee_options": [{"employee_id": None, "name": "Unassigned"}],
            }

        cur.execute("""
            SELECT employee_id, name
            FROM Employees
            WHERE upload_id = %s
            ORDER BY name ASC;
        """, (upload_id,))
        employee_rows = cur.fetchall()

        cur.execute("""
            SELECT
                a.assignment_id,
                a.employee_id,
                a.title,
                a.start_date,
                a.end_date,
                e.name
            FROM Assignments a
            LEFT JOIN Employees e ON a.employee_id = e.employee_id
            WHERE a.upload_id = %s
              AND a.start_date <= %s
              AND a.end_date >= %s
            ORDER BY e.name NULLS LAST, a.start_date ASC;
        """, (upload_id, week_end_day, week_start_day))
        rows = cur.fetchall()

        employees = {}
        unassigned = []

        for row in rows:
            payload = build_task_payload(row, week_start_day, week_end_day)
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

        employee_list = list(employees.values())
        employee_list.sort(key=lambda item: item["name"].lower())
        unassigned.sort(key=lambda item: item["title"].lower())

        employee_options = [{"employee_id": None, "name": "Unassigned"}]
        employee_options.extend([
            {"employee_id": emp_id, "name": name}
            for emp_id, name in employee_rows
        ])

        return {
            "week_start": str(week_start_day),
            "week_end": str(week_end_day),
            "employees": employee_list,
            "unassigned": unassigned,
            "employee_options": employee_options,
        }

    finally:
        cur.close()
        conn.close()


@router.post("/tasks")
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if payload.start_date > payload.end_date:
        raise HTTPException(400, "start date cannot be after end date")

    conn = get_connection()
    cur = conn.cursor()

    try:
        upload_id = get_active_upload_id(cur, payload.user_id)
        if not upload_id:
            raise HTTPException(400, "no active upload found for this user")

        employee_id = payload.employee_id
        if employee_id is not None:
            cur.execute("""
                SELECT 1
                FROM Employees
                WHERE employee_id = %s AND upload_id = %s;
            """, (employee_id, upload_id))
            if not cur.fetchone():
                raise HTTPException(404, "employee not found for this upload")

        cur.execute("""
            INSERT INTO Assignments (
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
        """, (
            employee_id,
            upload_id,
            title,
            payload.start_date,
            payload.end_date,
        ))

        assignment_id = cur.fetchone()[0]
        conn.commit()
        return {"assignment_id": assignment_id}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(500, str(exc))
    finally:
        cur.close()
        conn.close()
