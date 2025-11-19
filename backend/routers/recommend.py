from fastapi import APIRouter, HTTPException
from processing.recommend_engine import compute_recommendations

router = APIRouter()

@router.post("/recommend")
def recommend_task(data: dict):
    task = data.get("task_description")
    start = data.get("start_date")
    end = data.get("end_date")

    if not task:
        raise HTTPException(400, "task_description is required.")
    if not start or not end:
        raise HTTPException(400, "start_date and end_date are required.")

    return compute_recommendations(task, start, end)
