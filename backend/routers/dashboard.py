from fastapi import APIRouter, HTTPException
from processing.dashboard_processing import get_dashboard_summary

router = APIRouter()

@router.get("/dashboard/summary")
def dashboard_summary():
    try:
        data = get_dashboard_summary()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
