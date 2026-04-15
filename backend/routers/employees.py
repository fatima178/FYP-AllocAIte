from fastapi import APIRouter, HTTPException

from processing.employee.employee_processing import (
    EmployeeProcessingError,
    add_skills_to_employee,
    create_employee_entry,
    list_employees,
)

router = APIRouter()


def _required_positive_int(value, field_name: str) -> int:
    # shared validation for ids coming from flexible dict payloads
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, f"{field_name} must be a valid integer")
    if parsed <= 0:
        raise HTTPException(400, f"{field_name} must be greater than 0")
    return parsed


@router.get("/employees")
def get_employees(user_id: int):
    # list manager-owned employees for settings/team pages
    try:
        return {"employees": list_employees(user_id)}
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/employees")
def create_employee(payload: dict):
    # create one employee manually instead of through excel upload
    user_id = _required_positive_int(payload.get("user_id"), "user_id")
    try:
        return create_employee_entry(user_id, payload)
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.put("/employees/{employee_id}/skills")
def update_employee_skills(employee_id: int, payload: dict):
    # add or update skills for an existing employee
    user_id = _required_positive_int(payload.get("user_id"), "user_id")
    skills = payload.get("skills")
    try:
        return add_skills_to_employee(user_id, int(employee_id), skills)
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)
