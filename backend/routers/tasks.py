from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from processing.task_processing import (
    TaskProcessingError,
    create_task_entry,
    fetch_weekly_tasks,
)

router = APIRouter()


class TaskCreate(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1)
    start_date: date
    end_date: date
    employee_id: Optional[int] = None
@router.get("/tasks/week")
def get_weekly_tasks(user_id: int, week_start: Optional[date] = Query(None)):
    try:
        return fetch_weekly_tasks(user_id, week_start)
    except TaskProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/tasks")
def create_task(payload: TaskCreate):
    try:
        return create_task_entry(
            payload.user_id,
            payload.title,
            payload.start_date,
            payload.end_date,
            payload.employee_id,
        )
    except TaskProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)
