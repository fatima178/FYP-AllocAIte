from datetime import date
from fastapi import APIRouter, HTTPException

from processing.employee.employee_profile_common import EmployeeProfileError
from processing.employee.employee_profile_read_processing import (
    get_employee_profile,
    get_employee_recommendation_reason,
    get_employee_settings,
)
from processing.employee.employee_profile_skills_processing import (
    update_employee_self_skills,
    delete_employee_skill,
    fetch_pending_skill_requests,
    review_pending_skill_request,
)
from processing.employee.employee_profile_preferences_processing import (
    update_learning_goals,
    update_preferences,
)
from processing.employee.employee_calendar_processing import (
    EmployeeCalendarError,
    fetch_employee_calendar,
    create_personal_calendar_entry,
)
from schemas.employee_portal import (
    EmployeeCalendarEntryRequest,
    EmployeeLearningGoalsRequest,
    EmployeePreferencesRequest,
    EmployeeRecommendationReasonRequest,
    EmployeeSkillReviewRequest,
    EmployeeSkillsUpdateRequest,
)

router = APIRouter()


@router.get("/employee/profile")
def employee_profile(user_id: int):
    try:
        return get_employee_profile(int(user_id))
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.get("/employee/settings")
def employee_settings(user_id: int):
    try:
        return get_employee_settings(int(user_id))
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.put("/employee/skills")
def employee_update_skills(payload: EmployeeSkillsUpdateRequest):
    try:
        return update_employee_self_skills(payload.user_id, payload.skills)
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.delete("/employee/skills")
def employee_delete_skill(user_id: int, skill_name: str, skill_type: str):
    if not user_id:
        raise HTTPException(400, "user_id is required")
    if not skill_name:
        raise HTTPException(400, "skill_name is required")
    if not skill_type:
        raise HTTPException(400, "skill_type is required")
    try:
        return delete_employee_skill(int(user_id), skill_name, skill_type)
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.get("/employee/skills/pending")
def employee_pending_skills(user_id: int):
    if not user_id:
        raise HTTPException(400, "user_id is required")
    try:
        return fetch_pending_skill_requests(int(user_id))
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employee/skills/review")
def employee_review_skill(payload: EmployeeSkillReviewRequest):
    try:
        return review_pending_skill_request(payload.user_id, payload.request_id, payload.approve)
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.put("/employee/learning-goals")
def employee_update_learning_goals(payload: EmployeeLearningGoalsRequest):
    try:
        return update_learning_goals(payload.user_id, payload.learning_goals)
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.put("/employee/preferences")
def employee_update_preferences(payload: EmployeePreferencesRequest):
    preferences = payload.preferences
    if preferences is None:
        preferences = payload.preferences_text
    if preferences is None:
        preferences = payload.growth_text
    if preferences is None:
        raise HTTPException(400, "preferences_text is required")
    try:
        return update_preferences(payload.user_id, preferences)
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employee/recommendation-reason")
def employee_recommendation_reason(payload: EmployeeRecommendationReasonRequest):
    try:
        return get_employee_recommendation_reason(
            payload.user_id,
            payload.task_description,
            payload.start_date.isoformat(),
            payload.end_date.isoformat(),
        )
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.get("/employee/calendar")
def employee_calendar(user_id: int, week_start: date = None):
    try:
        return fetch_employee_calendar(int(user_id), week_start)
    except EmployeeCalendarError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employee/calendar")
def employee_calendar_entry(payload: EmployeeCalendarEntryRequest):
    try:
        return create_personal_calendar_entry(
            payload.user_id,
            payload.label,
            payload.start_date,
            payload.end_date,
            payload.total_hours,
        )
    except EmployeeCalendarError as exc:
        raise HTTPException(exc.status_code, exc.message)
