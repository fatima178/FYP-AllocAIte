from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from io import BytesIO

from processing.settings.settings_processing import (
    change_user_password,
    fetch_user_settings,
    persist_user_settings,
    update_account_details as process_account_details,
    verify_user_password,
)
from processing.uploads.export_processing import export_manager_data
from processing.recommendations.recommendation_log_processing import (
    RecommendationLogError,
    fetch_recommendation_history,
)
from schemas.settings import (
    ChangePasswordRequest,
    SettingsUpdateRequest,
    UpdateDetailsRequest,
    VerifyPasswordRequest,
)

router = APIRouter()


@router.get("/settings")
def get_settings(user_id: int):
    # return profile information and ui preferences for a user
    return fetch_user_settings(user_id)


@router.post("/settings")
def update_settings(payload: SettingsUpdateRequest):
    # save appearance settings and optional recommendation weight changes
    return persist_user_settings(
        payload.user_id,
        payload.theme,
        payload.font_size,
        payload.use_custom_weights,
        payload.weights,
    )


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


@router.get("/settings/export")
def export_settings(user_id: int):
    # export the manager's data as an excel file for backup/download
    content = export_manager_data(user_id)
    filename = "allocaite_export.xlsx"
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'},
    )


@router.get("/settings/recommendation-history")
def get_recommendation_history(
    user_id: int,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # paginated recommendation history for the settings/history panel
    try:
        return fetch_recommendation_history(user_id, limit, offset)
    except RecommendationLogError as exc:
        raise HTTPException(exc.status_code, exc.message)
