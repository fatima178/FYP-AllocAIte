from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from processing.settings_processing import (
    change_user_password,
    fetch_user_settings,
    persist_user_settings,
    update_account_details as process_account_details,
    verify_user_password,
)

router = APIRouter()


# pydantic model for updating account details
# fields not provided stay unchanged
class UpdateDetailsRequest(BaseModel):
    user_id: int
    name: Optional[str] = None
    email: Optional[EmailStr] = None


# pydantic model for password change requests
# carries both the old password and the new one
class ChangePasswordRequest(BaseModel):
    user_id: int
    current_password: str
    new_password: str


# pydantic model used when only verifying a password
class VerifyPasswordRequest(BaseModel):
    user_id: int
    current_password: str


@router.get("/settings")
def get_settings(user_id: int):
    # return profile information and ui preferences for a user
    return fetch_user_settings(user_id)


@router.post("/settings")
def update_settings(data: dict):
    # user settings (theme and font size) come in as a raw dict
    user_id = data.get("user_id")
    theme = data.get("theme")
    font_size = data.get("font_size")

    if not user_id:
        raise HTTPException(400, "user_id is required")

    # persist_user_settings updates only the fields passed
    return persist_user_settings(int(user_id), theme, font_size)


@router.put("/settings/details")
def update_account_details(payload: UpdateDetailsRequest):
    # user must supply at least one field: name or email
    if payload.name is None and payload.email is None:
        raise HTTPException(400, "no changes supplied.")

    # forwards the update to the settings_processing module
    return process_account_details(payload.user_id, payload.name, payload.email)


@router.post("/settings/password/verify")
def verify_password(payload: VerifyPasswordRequest):
    # checks whether the provided current password is correct
    return verify_user_password(payload.user_id, payload.current_password)


@router.post("/settings/password")
def change_password(payload: ChangePasswordRequest):
    # applies password change after verifying current password
    return change_user_password(
        payload.user_id,
        payload.current_password,
        payload.new_password
    )
