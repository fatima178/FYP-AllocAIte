from datetime import date
from fastapi import APIRouter, HTTPException

from processing.employee_profile_processing import (
    EmployeeProfileError,
    get_employee_profile,
    get_employee_recommendation_reason,
    get_employee_settings,
    update_employee_self_skills,
    update_learning_goals,
    update_preferences,
)
from processing.employee_calendar_processing import (
    EmployeeCalendarError,
    fetch_employee_calendar,
    create_personal_calendar_entry,
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
def employee_update_skills(payload: dict):
    user_id = payload.get("user_id")
    skills = payload.get("skills")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    try:
        return update_employee_self_skills(int(user_id), skills)
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.put("/employee/learning-goals")
def employee_update_learning_goals(payload: dict):
    user_id = payload.get("user_id")
    goals = payload.get("learning_goals")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    try:
        return update_learning_goals(int(user_id), goals)
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.put("/employee/preferences")
def employee_update_preferences(payload: dict):
    user_id = payload.get("user_id")
    preferences = payload.get("preferences")
    if preferences is None:
        preferences = payload.get("preferences_text")
    if preferences is None:
        preferences = payload.get("growth_text")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    if preferences is None:
        raise HTTPException(400, "preferences_text is required")
    try:
        return update_preferences(int(user_id), preferences)
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employee/recommendation-reason")
def employee_recommendation_reason(payload: dict):
    user_id = payload.get("user_id")
    task_description = payload.get("task_description")
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    if not task_description:
        raise HTTPException(400, "task_description is required")
    if not start_date or not end_date:
        raise HTTPException(400, "start_date and end_date are required")
    try:
        return get_employee_recommendation_reason(
            int(user_id),
            task_description,
            start_date,
            end_date,
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
def employee_calendar_entry(payload: dict):
    user_id = payload.get("user_id")
    label = payload.get("label")
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    if not start_date or not end_date:
        raise HTTPException(400, "start_date and end_date are required")
    try:
        start_dt = date.fromisoformat(str(start_date))
        end_dt = date.fromisoformat(str(end_date))
        return create_personal_calendar_entry(int(user_id), label, start_dt, end_dt)
    except ValueError:
        raise HTTPException(400, "start_date and end_date must be valid ISO dates")
    except EmployeeCalendarError as exc:
        raise HTTPException(exc.status_code, exc.message)
