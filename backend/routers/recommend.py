from fastapi import APIRouter, HTTPException

from processing.recommendations.recommend_processing import (
    RecommendationError,
    generate_recommendations,
)
from processing.recommendations.recommend_assignment import assign_recommended_task
from processing.recommendations.recommendation_log_processing import (
    RecommendationLogError,
    attach_assignment_to_task,
    clear_recommendation_feedback,
    mark_manager_selected,
    submit_recommendation_feedback,
)
from schemas.recommend import (
    RecommendationAssignRequest,
    RecommendationFeedbackRequest,
    RecommendationRequest,
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
def recommend_task(payload: RecommendationRequest):
    if payload.start_date > payload.end_date:
        raise HTTPException(400, "start_date must be on or before end_date")

    try:
        return generate_recommendations(
            payload.task_description,
            payload.start_date.isoformat(),
            payload.end_date.isoformat(),
            payload.user_id,
            payload.upload_id,
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
def assign_recommendation(payload: RecommendationAssignRequest):
    if payload.start_date > payload.end_date:
        raise HTTPException(400, "start_date must be on or before end_date")
    try:
        result = assign_recommended_task(
            payload.user_id,
            payload.employee_id,
            payload.task_description,
            payload.start_date.isoformat(),
            payload.end_date.isoformat(),
            payload.total_hours,
            payload.upload_id,
        )

        if payload.task_id is not None:
            try:
                mark_manager_selected(payload.user_id, payload.task_id, payload.employee_id)
                attach_assignment_to_task(
                    payload.user_id,
                    payload.task_id,
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
def submit_feedback(payload: RecommendationFeedbackRequest):
    try:
        submit_recommendation_feedback(
            payload.user_id,
            payload.task_id,
            payload.employee_id,
            payload.performance_rating,
            str(payload.feedback_notes).strip() if payload.feedback_notes is not None else None,
            payload.outcome_tags,
        )
        return {"message": "Feedback submitted successfully."}
    except RecommendationLogError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.delete("/recommend/feedback")
def clear_feedback(user_id: int, task_id: int, employee_id: int):
    if not user_id or not task_id or not employee_id:
        raise HTTPException(400, "user_id, task_id, and employee_id are required")

    try:
        clear_recommendation_feedback(int(user_id), int(task_id), int(employee_id))
        return {"message": "Feedback cleared successfully."}
    except RecommendationLogError as exc:
        raise HTTPException(exc.status_code, exc.message)
