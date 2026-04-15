from fastapi import APIRouter, HTTPException

from processing.employee.employee_processing import (
    EmployeeProcessingError,
    add_skills_to_employee,
    create_employee_entry,
    list_employees,
)

router = APIRouter()


def _required_positive_int(value, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, f"{field_name} must be a valid integer")
    if parsed <= 0:
        raise HTTPException(400, f"{field_name} must be greater than 0")
    return parsed


@router.get("/employees")
def get_employees(user_id: int):
    try:
        return {"employees": list_employees(user_id)}
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employees")
def create_employee(payload: dict):
    user_id = _required_positive_int(payload.get("user_id"), "user_id")
    try:
        return create_employee_entry(user_id, payload)
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.put("/employees/{employee_id}/skills")
def update_employee_skills(employee_id: int, payload: dict):
    user_id = _required_positive_int(payload.get("user_id"), "user_id")
    skills = payload.get("skills")
    try:
        return add_skills_to_employee(user_id, int(employee_id), skills)
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)
