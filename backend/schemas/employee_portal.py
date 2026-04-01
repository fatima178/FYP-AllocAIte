from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EmployeeSkillsUpdateRequest(BaseModel):
    user_id: int
    skills: Optional[List[Dict[str, Any]]] = None


class EmployeeSkillReviewRequest(BaseModel):
    user_id: int
    request_id: int
    approve: bool


class EmployeeLearningGoalsRequest(BaseModel):
    user_id: int
    learning_goals: Optional[List[Dict[str, Any]]] = None


class EmployeePreferencesRequest(BaseModel):
    user_id: int
    preferences: Optional[Dict[str, Any]] = None
    preferences_text: Optional[str] = None
    growth_text: Optional[str] = None


class EmployeeRecommendationReasonRequest(BaseModel):
    user_id: int
    task_description: str = Field(..., min_length=1)
    start_date: date
    end_date: date


class EmployeeCalendarEntryRequest(BaseModel):
    user_id: int
    label: Optional[str] = None
    start_date: date
    end_date: date
