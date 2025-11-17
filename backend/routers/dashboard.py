from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from processing.dashboard_processing import get_dashboard_summary, get_employees_data, get_available_skills

router = APIRouter()

@router.get("/dashboard/summary")
def dashboard_summary(user_id: int):
    try:
        return get_dashboard_summary(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/employees")
def dashboard_employees(
    user_id: int,
    search: Optional[str] = None,
    skills: Optional[List[str]] = Query(None),
    availability: Optional[str] = None,
):
    try:
        return get_employees_data(user_id, search, skills, availability)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/skills")
def dashboard_skills(user_id: int):
    try:
        return get_available_skills(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
