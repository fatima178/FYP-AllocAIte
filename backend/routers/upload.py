from fastapi import APIRouter, HTTPException, File, Form, UploadFile

from processing.assignment_upload_processing import (
    AssignmentUploadError,
    process_assignment_upload,
)

router = APIRouter()

@router.post("/upload")
async def upload_excel(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    column_map: str = Form(None),
):
    file_bytes = await file.read()
    try:
        return process_assignment_upload(user_id, file.filename, file_bytes, column_map)
    except AssignmentUploadError as exc:
        raise HTTPException(exc.status_code, exc.message)
