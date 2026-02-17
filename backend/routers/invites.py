from fastapi import APIRouter, HTTPException

from processing.invite_processing import (
    InviteProcessingError,
    create_invite,
    accept_invite,
    get_invite_info,
)

router = APIRouter()


@router.post("/invites")
def create_employee_invite(payload: dict):
    user_id = payload.get("user_id")
    employee_id = payload.get("employee_id")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    if not employee_id:
        raise HTTPException(400, "employee_id is required")
    try:
        return create_invite(int(user_id), int(employee_id))
    except InviteProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)


@router.post("/invites/accept")
def accept_employee_invite(payload: dict):
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
    try:
        return get_invite_info(token)
    except InviteProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)
