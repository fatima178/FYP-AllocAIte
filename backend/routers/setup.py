from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from db import get_connection
from processing.setup_import_processing import (
    SetupImportError,
    process_employee_setup_import,
)

router = APIRouter()


@router.get("/setup/status")
def setup_status(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT COUNT(*) FROM "Employees" WHERE user_id = %s;', (user_id,))
        count = cur.fetchone()[0]
        return {
            "employee_count": count,
            "can_import": count == 0,
        }
    finally:
        cur.close()
        conn.close()


@router.post("/setup/import-employees")
async def import_employees(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    preview: bool = Form(False),
    column_map: str = Form(None),
):
    file_bytes = await file.read()
    try:
        return process_employee_setup_import(
            user_id,
            file.filename,
            file_bytes,
            column_map,
            preview,
        )
    except SetupImportError as exc:
        raise HTTPException(exc.status_code, exc.message)
