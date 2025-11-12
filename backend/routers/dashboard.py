from fastapi import APIRouter, HTTPException
from processing.dashboard_processing import get_dashboard_summary, get_employees_data

router = APIRouter()

@router.get("/dashboard/summary")
def dashboard_summary():
    try:
        return get_dashboard_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/employees")
def dashboard_employees():
    try:
        return get_employees_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
