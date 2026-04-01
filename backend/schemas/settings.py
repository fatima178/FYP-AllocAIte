from typing import Dict, Optional

from pydantic import BaseModel, EmailStr


class SettingsUpdateRequest(BaseModel):
    user_id: int
    theme: Optional[str] = None
    font_size: Optional[str] = None
    use_custom_weights: Optional[bool] = None
    weights: Optional[Dict[str, float]] = None


class UpdateDetailsRequest(BaseModel):
    user_id: int
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    user_id: int
    current_password: str
    new_password: str


class VerifyPasswordRequest(BaseModel):
    user_id: int
    current_password: str
