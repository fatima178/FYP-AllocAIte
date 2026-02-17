from fastapi import APIRouter, HTTPException

from processing.employee_profile_processing import (
    EmployeeProfileError,
    get_employee_profile,
    update_employee_self_skills,
    update_learning_goals,
    update_preferences,
)

router = APIRouter()


@router.get("/employee/profile")
def employee_profile(user_id: int):
    try:
        return get_employee_profile(int(user_id))
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
    if not user_id:
        raise HTTPException(400, "user_id is required")
    if not isinstance(preferences, dict):
        raise HTTPException(400, "preferences must be an object")
    try:
        return update_preferences(int(user_id), preferences)
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)
