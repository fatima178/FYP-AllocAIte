from fastapi import APIRouter, HTTPException

from processing.invite_processing import (
    InviteProcessingError,
    create_invite,
    accept_invite,
    get_invite_info,
)

router = APIRouter()


def _required_positive_int(value, field_name: str) -> int:
    # ids from invite payloads need to be valid positive integers
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, f"{field_name} must be a valid integer")
    if parsed <= 0:
        raise HTTPException(400, f"{field_name} must be greater than 0")
    return parsed


@router.post("/invites")
def create_employee_invite(payload: dict):
    # manager creates a login invite for one employee
    user_id = _required_positive_int(payload.get("user_id"), "user_id")
    employee_id = _required_positive_int(payload.get("employee_id"), "employee_id")
    try:
        return create_invite(user_id, employee_id)
    except InviteProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/invites/accept")
def accept_employee_invite(payload: dict):
    # employee accepts their invite and creates login details
    token = payload.get("token")
    email = payload.get("email")
    password = payload.get("password")
    if not token:
        raise HTTPException(400, "token is required")
    if not email:
        raise HTTPException(400, "email is required")
    if not password:
        raise HTTPException(400, "password is required")
    try:
        return accept_invite(token, email, password)
    except InviteProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.get("/invites/info")
def invite_info(token: str):
    # frontend uses this to show who the invite is for
    try:
        return get_invite_info(token)
    except InviteProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)
