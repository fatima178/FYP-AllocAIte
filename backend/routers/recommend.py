from fastapi import APIRouter, HTTPException

from processing.recommend_processing import (
    RecommendationError,
    generate_recommendations,
    resolve_upload_id,
)
from processing.recommend_assignment import assign_recommended_task

router = APIRouter()


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

    try:
        return generate_recommendations(
            task,
            start,
            end,
            int(user_id) if user_id is not None else None,
            int(upload_id) if upload_id is not None else None,
        )
    except RecommendationError as exc:
        raise HTTPException(exc.status_code, exc.message)


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
        resolved_upload_id = resolve_upload_id(
            int(user_id),
            int(upload_id) if upload_id is not None else None,
        )
        if not resolved_upload_id:
            raise ValueError("no uploads found for this user")

        result = assign_recommended_task(
            int(user_id),
            int(employee_id),
            title,
            start,
            end,
            resolved_upload_id,
        )
        return {"message": "Task assigned successfully.", **result}
    except ValueError as exc:
        raise HTTPException(400, str(exc))
