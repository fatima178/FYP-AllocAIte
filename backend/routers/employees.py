from fastapi import APIRouter, HTTPException

from processing.employee.employee_processing import (
    EmployeeProcessingError,
    add_skills_to_employee,
    create_employee_entry,
    list_employees,
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


@router.put("/employees/{employee_id}/skills")
def update_employee_skills(employee_id: int, payload: dict):
    user_id = payload.get("user_id")
    skills = payload.get("skills")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    try:
        return add_skills_to_employee(int(user_id), int(employee_id), skills)
    except EmployeeProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)
