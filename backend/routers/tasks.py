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


# pydantic model for creating a task
# includes basic validation such as non empty title and correct date types
class TaskCreate(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1)        # task name must be at least one character
    start_date: date                             # start date must be valid iso (handled by pydantic)
    end_date: date                               # same for end date
    employee_id: Optional[int] = None            # optional: allows unassigned tasks


@router.get("/tasks/week")
def get_weekly_tasks(user_id: int, week_start: Optional[date] = Query(None)):
    # fetch tasks for the specified week; if no week_start provided,
    # the service will normalize it to the current week's monday
    try:
        return fetch_weekly_tasks(user_id, week_start)
    except TaskProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/tasks")
def create_task(payload: TaskCreate):
    # create a new task with optional assignment to an employee
    # actual validation (date ordering, upload presence, etc.) handled by service layer
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
