from fastapi import APIRouter, HTTPException

from processing.employee_processing import (
    EmployeeProcessingError,
    create_employee_entry,
    list_employees,
    normalize_skill_entry,
    normalize_skill_lines,
)
from processing.employee_profile_processing import (
    EmployeeProfileError,
    create_employee_account,
)

router = APIRouter()


@router.get("/employees")
def get_employees(user_id: int):
    try:
        return {"employees": list_employees(user_id)}
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employees")
def create_employee(payload: dict):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    try:
        return create_employee_entry(int(user_id), payload)
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employees/skills/normalize")
def normalize_skill(payload: dict):
    name = payload.get("skill_name")
    years = payload.get("years_experience")
    try:
        return normalize_skill_entry(name, years)
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employees/skills/normalize-batch")
def normalize_skills(payload: dict):
    raw_text = payload.get("raw_text")
    try:
        return {"skills": normalize_skill_lines(raw_text)}
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employees/create-login")
def create_employee_login(payload: dict):
    user_id = payload.get("user_id")
    employee_id = payload.get("employee_id")
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    if not employee_id:
        raise HTTPException(400, "employee_id is required")
    if not name or not email or not password:
        raise HTTPException(400, "name, email, and password are required")
    try:
        return create_employee_account(
            int(user_id),
            int(employee_id),
            name,
            email,
            password,
        )
    except EmployeeProfileError as exc:
        raise HTTPException(exc.status_code, exc.message)
