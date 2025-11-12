from db import get_connection
from datetime import date
import json
import pandas as pd
from io import BytesIO
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from processing.availability_processing import calculate_availability  # availability helper

router = APIRouter()

# required columns for uploads
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
    # check file type
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx or .xls) are allowed.")

    # read excel file
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), sheet_name=0)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    # make sure all required columns exist
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing)}")

    conn = get_connection()
    cur = conn.cursor()
    try:
        # deactivate old uploads and clear their data
        cur.execute("UPDATE uploads SET is_active = FALSE;")
        cur.execute("DELETE FROM employees;")
        cur.execute("DELETE FROM assignments;")

        # record upload in uploads table
        cur.execute(
            """
            INSERT INTO Uploads (user_id, file_name, is_active)
            VALUES (%s, %s, TRUE)
            RETURNING upload_id;
            """,
            (user_id, file.filename),
        )
        upload_id = cur.fetchone()[0]

        # group rows by employee name to handle multiple assignments per person
        grouped = df.groupby("Employee Name")

        for name, group in grouped:
            first_row = group.iloc[0]
            availability_status = calculate_availability(first_row)

            # build list of all active assignments for this employee
            assignments = []
            for _, row in group.iterrows():
                start_date = pd.to_datetime(row.get("Start Date"), errors="coerce").date() if pd.notna(row.get("Start Date")) else None
                end_date = pd.to_datetime(row.get("End Date"), errors="coerce").date() if pd.notna(row.get("End Date")) else None

                if row.get("Current Project") and str(row.get("Current Project")).strip():
                    assignments.append({
                        "title": str(row["Current Project"]).strip(),
                        "start_date": str(start_date) if start_date and str(start_date) not in ["NaT", "nan", "None"] else None,
                        "end_date": str(end_date) if end_date and str(end_date) not in ["NaT", "nan", "None"] else None,
                        "total_hours": float(row.get("Total Hours", 0)) if not pd.isna(row.get("Total Hours")) else 0,
                        "remaining_hours": float(row.get("Remaining Hours", 0)) if not pd.isna(row.get("Remaining Hours")) else 0,
                        "priority": str(row.get("Priority", "")).strip(),
                    })

            # insert single employee record with multiple assignments stored in a list
            cur.execute(
                """
                INSERT INTO Employees (
                    upload_id,
                    name,
                    role,
                    department,
                    experience_years,
                    skills,
                    availability_status,
                    active_assignments
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    upload_id,
                    name,
                    first_row["Role"],
                    first_row["Department"],
                    float(first_row["Experience (Years)"]),
                    json.dumps(first_row["Skill Set"].split(",") if isinstance(first_row["Skill Set"], str) else []),
                    availability_status,
                    json.dumps(assignments) if assignments else None,
                ),
            )

        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving data: {exc}")
    finally:
        cur.close()
        conn.close()

    # return message to frontend
    return {"message": "File uploaded and availability processed.", "rows": len(df)}
