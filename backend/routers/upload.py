from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from db import get_connection

router = APIRouter()

# required columns
REQUIRED_COLUMNS = [
    "Employee Name",
    "Role",
    "Department",
    "Skill Set",
    "Experience (Years)",
    "Skill Level (1–5)",
    "Current Project",
    "Start Date",
    "End Date",
    "Total Hours",
    "Remaining Hours",
    "Priority",
]

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


@router.post("/upload")
async def upload_excel(user_id: int = Form(...), file: UploadFile = File(...)):
    # reject unsupported file types 
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx or .xls) are allowed.",
        )

    try:
        contents = await file.read()
        dataframe = pd.read_excel(BytesIO(contents), sheet_name=0)
    except Exception as exc:  
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read the uploaded Excel file: {exc}",
        ) from exc

    # Before touching the database, double check that every required column is present
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_columns)}",
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        # keep a trail of uploads for auditing, but skip row level inserts for now
        cur.execute(
            """
            INSERT INTO Uploads (user_id, file_name, is_active)
            VALUES (%s, %s, TRUE)
            RETURNING upload_id;
            """,
            (user_id, file.filename),
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not store upload metadata.",
        ) from exc
    finally:
        cur.close()
        conn.close()

    # share success message how large the file was
    return {
        "message": "File uploaded successfully",
        "rows": len(dataframe),
    }
