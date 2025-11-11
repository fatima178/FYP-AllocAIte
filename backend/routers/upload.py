from io import BytesIO
from pathlib import Path
import json
import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from db import get_connection
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

        # keep track of unique projects
        seen_projects = set()

        # go through each row and calculate availability
        for _, row in df.iterrows():
            availability_status = calculate_availability(row)  # use helper

            # insert employee data
            cur.execute(
                """
                INSERT INTO Employees (upload_id, name, role, department, experience_years, skills, availability_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    upload_id,
                    row["Employee Name"],
                    row["Role"],
                    row["Department"],
                    float(row["Experience (Years)"]),
                    json.dumps(row["Skill Set"].split(",") if isinstance(row["Skill Set"], str) else []),
                    availability_status,
                ),
            )

            # inawer inro assignments
            project_title = str(row.get("Current Project", "")).strip()
            start_raw = row.get("Start Date")
            end_raw = row.get("End Date")

            # clean invalid dates like '—', NaN, or blanks
            def clean_date(v):
                if pd.isna(v) or str(v).strip() in ["—", "-", "", "NaT", "nan"]:
                    return None
                try:
                    return pd.to_datetime(v, errors="coerce").date()
                except Exception:
                    return None

            start_date = clean_date(start_raw)
            end_date = clean_date(end_raw)

            # insert project only once per upload
            if project_title and project_title not in seen_projects:
                cur.execute(
                    """
                    INSERT INTO Assignments (upload_id, title, start_date, end_date, description)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (
                        upload_id,
                        project_title,
                        start_date,
                        end_date,
                        f"Imported from {file.filename}",
                    ),
                )
                seen_projects.add(project_title)
        

        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving data: {exc}")
    finally:
        cur.close()
        conn.close()

    # return message to frontend
    return {"message": "File uploaded and availability processed.", "rows": len(df)}
