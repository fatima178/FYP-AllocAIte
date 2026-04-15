from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class RecommendationRequest(BaseModel):
    # request body for generating ranked employee recommendations
    task_description: str = Field(..., min_length=1)
    user_id: int = Field(..., gt=0)
    upload_id: Optional[int] = Field(None, gt=0)
    start_date: date
    end_date: date

    @field_validator("task_description")
    @classmethod
    def task_description_must_not_be_blank(cls, value):
        # pydantic min_length does not catch strings that are only spaces
        if not value.strip():
            raise ValueError("task_description is required")
        return value.strip()


class RecommendationAssignRequest(BaseModel):
    # request body for assigning a recommended employee to the task
    user_id: int = Field(..., gt=0)
    employee_id: int = Field(..., gt=0)
    task_description: str = Field(..., min_length=1)
    start_date: date
    end_date: date
    total_hours: float = Field(..., gt=0)
    upload_id: Optional[int] = Field(None, gt=0)
    task_id: Optional[int] = Field(None, gt=0)

    @field_validator("task_description")
    @classmethod
    def assignment_description_must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError("task_description is required")
        return value.strip()


class RecommendationFeedbackRequest(BaseModel):
    # feedback saved after a recommended assignment is completed
    user_id: int = Field(..., gt=0)
    task_id: int = Field(..., gt=0)
    employee_id: int = Field(..., gt=0)
    performance_rating: str = Field(..., min_length=1)
    feedback_notes: Optional[str] = None
    outcome_tags: Optional[List[str]] = None

    @field_validator("performance_rating")
    @classmethod
    def rating_must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError("performance_rating is required")
        return value.strip()
