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

# -------------------------------------
# GET USER SETTINGS
# -------------------------------------
@router.get("/settings")
def get_settings(user_id: int):
    return fetch_user_settings(user_id)


# -------------------------------------
# UPDATE USER SETTINGS
# -------------------------------------
@router.post("/settings")
def update_settings(data: dict):
    user_id = data.get("user_id")
    theme = data.get("theme")
    font_size = data.get("font_size")

    if not user_id:
        raise HTTPException(400, "user_id is required")

    return persist_user_settings(int(user_id), theme, font_size)


# -------------------------------------
# UPDATE ACCOUNT DETAILS
# -------------------------------------
@router.put("/settings/details")
def update_account_details(payload: UpdateDetailsRequest):
    if payload.name is None and payload.email is None:
        raise HTTPException(400, "No changes supplied.")

    return process_account_details(payload.user_id, payload.name, payload.email)


# -------------------------------------
# CHANGE PASSWORD
# -------------------------------------
@router.post("/settings/password/verify")
def verify_password(payload: VerifyPasswordRequest):
    return verify_user_password(payload.user_id, payload.current_password)


@router.post("/settings/password")
def change_password(payload: ChangePasswordRequest):
    return change_user_password(payload.user_id, payload.current_password, payload.new_password)
