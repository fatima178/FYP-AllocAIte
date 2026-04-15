from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class EmployeeSkillsUpdateRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    skills: Optional[List[Dict[str, Any]]] = None


class EmployeeSkillReviewRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    request_id: int = Field(..., gt=0)
    approve: bool


class EmployeeLearningGoalsRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    learning_goals: Optional[List[Dict[str, Any]]] = None


class EmployeePreferencesRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    preferences: Optional[Dict[str, Any]] = None
    preferences_text: Optional[str] = None
    growth_text: Optional[str] = None


class EmployeeRecommendationReasonRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    task_description: str = Field(..., min_length=1)
    start_date: date
    end_date: date

    @field_validator("task_description")
    @classmethod
    def task_description_must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError("task_description is required")
        return value.strip()


class EmployeeCalendarEntryRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    label: Optional[str] = None
    start_date: date
    end_date: date
    total_hours: float = Field(..., gt=0)
