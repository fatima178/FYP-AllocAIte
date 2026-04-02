from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    task_description: str = Field(..., min_length=1)
    user_id: int
    upload_id: Optional[int] = None
    start_date: date
    end_date: date


class RecommendationAssignRequest(BaseModel):
    user_id: int
    employee_id: int
    task_description: str = Field(..., min_length=1)
    start_date: date
    end_date: date
    total_hours: float = Field(..., gt=0)
    upload_id: Optional[int] = None
    task_id: Optional[int] = None


class RecommendationFeedbackRequest(BaseModel):
    user_id: int
    task_id: int
    employee_id: int
    performance_rating: str = Field(..., min_length=1)
    feedback_notes: Optional[str] = None
    outcome_tags: Optional[List[str]] = None
