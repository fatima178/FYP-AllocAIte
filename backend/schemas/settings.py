from typing import Dict, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class SettingsUpdateRequest(BaseModel):
    # settings form can update appearance, custom weights, or both
    user_id: int = Field(..., gt=0)
    theme: Optional[str] = None
    font_size: Optional[str] = None
    use_custom_weights: Optional[bool] = None
    weights: Optional[Dict[str, float]] = None

    @field_validator("theme")
    @classmethod
    def theme_must_be_known(cls, value):
        if value is not None and value not in {"light", "dark"}:
            raise ValueError("theme must be light or dark")
        return value

    @field_validator("font_size")
    @classmethod
    def font_size_must_be_known(cls, value):
        if value is not None and value not in {"small", "medium", "large"}:
            raise ValueError("font_size must be small, medium, or large")
        return value


class UpdateDetailsRequest(BaseModel):
    # account details update, fields are optional because user may change one value
    user_id: int = Field(..., gt=0)
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    # password change needs the current and replacement passwords
    user_id: int = Field(..., gt=0)
    current_password: str
    new_password: str


class VerifyPasswordRequest(BaseModel):
    # used before allowing sensitive account changes
    user_id: int = Field(..., gt=0)
    current_password: str
