from fastapi import APIRouter, HTTPException, File, Form, UploadFile

from processing.upload_processing import (
    UploadProcessingError,
    process_upload,
)

router = APIRouter()

@router.post("/upload")
async def upload_excel(user_id: int = Form(...), file: UploadFile = File(...)):
    file_bytes = await file.read()
    try:
        return process_upload(user_id, file.filename, file_bytes)
    except UploadProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message)
