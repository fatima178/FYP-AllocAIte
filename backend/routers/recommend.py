from datetime import datetime
from fastapi import APIRouter, HTTPException

from processing.recommend_processing import (
    RecommendationError,
    generate_recommendations,
)
from processing.recommend_assignment import assign_recommended_task
from processing.recommendation_log_processing import (
    RecommendationLogError,
    attach_assignment_to_task,
    mark_manager_selected,
    submit_recommendation_feedback,
)

router = APIRouter()


# ----------------------------------------------------------
# generate recommendations for a task
# ----------------------------------------------------------
# validates:
#   - task description present
#   - user_id + upload_id integers if provided
#   - start/end dates valid ISO format and ordered correctly
# calls the matching pipeline and returns ranked recommendations.
@router.post("/recommend")
def recommend_task(data: dict):
    task = data.get("task_description")
    upload_id = data.get("upload_id")
    user_id = data.get("user_id")
    start = data.get("start_date")
    end = data.get("end_date")

    # required fields
    if not task:
        raise HTTPException(400, "task_description is required")
    if not start or not end:
        raise HTTPException(400, "start_date and end_date are required")

    # validate user_id
    try:
        resolved_user_id = int(user_id) if user_id is not None else None
    except (TypeError, ValueError):
        raise HTTPException(400, "user_id must be an integer")

    # validate upload_id (metadata only)
    try:
        resolved_upload_id = int(upload_id) if upload_id is not None else None
    except (TypeError, ValueError):
        raise HTTPException(400, "upload_id must be an integer")

    # validate date format
    try:
        start_dt = datetime.fromisoformat(start).date()
        end_dt = datetime.fromisoformat(end).date()
    except ValueError:
        raise HTTPException(
            400,
            "start_date and end_date must be valid ISO dates (yyyy-mm-dd)"
        )

    if start_dt > end_dt:
        raise HTTPException(400, "start_date must be on or before end_date")

    # run recommendation engine
    try:
        return generate_recommendations(
            task,
            start_dt.isoformat(),
            end_dt.isoformat(),
            resolved_user_id,
            None,
        )
    except RecommendationError as exc:
        raise HTTPException(exc.status_code, exc.message)


# ----------------------------------------------------------
# assign a recommended task to a specific employee
# ----------------------------------------------------------
# validates:
#   - user_id, employee_id, title, dates provided
#   - resolves correct upload for user
# inserts assignment via assign_recommended_task().
@router.post("/recommend/assign")
def assign_recommendation(data: dict):
    user_id = data.get("user_id")
    employee_id = data.get("employee_id")
    title = data.get("task_description")
    start = data.get("start_date")
    end = data.get("end_date")
    upload_id = data.get("upload_id")
    task_id = data.get("task_id")

    # required fields
    if not user_id:
        raise HTTPException(400, "user_id is required")
    if not employee_id:
        raise HTTPException(400, "employee_id is required")
    if not title:
        raise HTTPException(400, "task_description is required")
    if not start or not end:
        raise HTTPException(400, "start_date and end_date are required")

    try:
        # create assignment
        result = assign_recommended_task(
            int(user_id),
            int(employee_id),
            title,
            start,
            end,
            None,
        )

        # mark which recommendation was selected (if task_id provided)
        if task_id is not None:
            try:
                mark_manager_selected(int(user_id), int(task_id), int(employee_id))
                attach_assignment_to_task(
                    int(user_id),
                    int(task_id),
                    int(result.get("assignment_id")),
                )
            except RecommendationLogError:
                pass

        return {"message": "Task assigned successfully.", **result}

    except ValueError as exc:
        raise HTTPException(400, str(exc))


# ----------------------------------------------------------
# submit feedback for a completed assignment
# ----------------------------------------------------------
@router.post("/recommend/feedback")
def submit_feedback(data: dict):
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    employee_id = data.get("employee_id")
    rating = data.get("performance_rating")
    notes = data.get("feedback_notes")

    if not user_id or not task_id or not employee_id:
        raise HTTPException(400, "user_id, task_id, and employee_id are required")
    if not rating:
        raise HTTPException(400, "performance_rating is required")

    try:
        submit_recommendation_feedback(
            int(user_id),
            int(task_id),
            int(employee_id),
            str(rating),
            str(notes).strip() if notes is not None else None,
        )
        return {"message": "Feedback submitted successfully."}
    except RecommendationLogError as exc:
        raise HTTPException(exc.status_code, exc.message)
