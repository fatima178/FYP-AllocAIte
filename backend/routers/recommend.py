from typing import Optional

from fastapi import APIRouter, HTTPException

from db import get_connection
from processing.nlp.task_matching import match_employees
from processing.recommend_assignment import assign_recommended_task

router = APIRouter()


def resolve_upload_id(user_id: Optional[int], upload_id: Optional[int]) -> Optional[int]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        if upload_id is not None:
            if user_id is None:
                return upload_id

            cur.execute(
                """
                SELECT upload_id
                FROM Uploads
                WHERE upload_id = %s AND user_id = %s;
                """,
                (upload_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "upload not found for this user")
            return row[0]

        if user_id is None:
            return None

        cur.execute(
            """
            SELECT upload_id
            FROM Uploads
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
            FROM Uploads
            WHERE user_id = %s
            ORDER BY upload_date DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None

    finally:
        cur.close()
        conn.close()


@router.post("/recommend")
def recommend_task(data: dict):
    task = data.get("task_description")
    upload_id = data.get("upload_id")
    user_id = data.get("user_id")
    start = data.get("start_date")
    end = data.get("end_date")

    if not task:
        raise HTTPException(400, "task_description is required")
    if not start or not end:
        raise HTTPException(400, "start_date and end_date are required")

    resolved_upload_id = resolve_upload_id(
        int(user_id) if user_id is not None else None,
        int(upload_id) if upload_id is not None else None,
    )
    if not resolved_upload_id:
        raise HTTPException(400, "no uploads found for this user")

    ranked = match_employees(task, resolved_upload_id, start, end)
    return ranked


@router.post("/recommend/assign")
def assign_recommendation(data: dict):
    user_id = data.get("user_id")
    employee_id = data.get("employee_id")
    title = data.get("task_description")
    start = data.get("start_date")
    end = data.get("end_date")
    upload_id = data.get("upload_id")

    if not user_id:
        raise HTTPException(400, "user_id is required")
    if not employee_id:
        raise HTTPException(400, "employee_id is required")
    if not title:
        raise HTTPException(400, "task_description is required")
    if not start or not end:
        raise HTTPException(400, "start_date and end_date are required")

    try:
        result = assign_recommended_task(
            int(user_id),
            int(employee_id),
            title,
            start,
            end,
            int(upload_id) if upload_id is not None else None,
        )
        return {"message": "Task assigned successfully.", **result}
    except ValueError as exc:
        raise HTTPException(400, str(exc))
