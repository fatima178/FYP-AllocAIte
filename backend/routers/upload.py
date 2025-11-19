# routers/upload.py

from fastapi import APIRouter, HTTPException, File, Form, UploadFile
from io import BytesIO
from pathlib import Path
import pandas as pd
import json

from db import get_connection

router = APIRouter()

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
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Only Excel files (.xlsx or .xls) are allowed.")

    try:
        df = pd.read_excel(BytesIO(await file.read()), sheet_name=0)
    except Exception as exc:
        raise HTTPException(400, f"Could not read file: {exc}")

    # Check required columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise HTTPException(400, f"Missing required columns: {', '.join(missing)}")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Deactivate previous uploads for this user
        cur.execute("UPDATE Uploads SET is_active = FALSE WHERE user_id = %s;", (user_id,))

        # Delete old employees and assignments for this user
        cur.execute("""
            DELETE FROM Employees
            WHERE upload_id IN (SELECT upload_id FROM Uploads WHERE user_id = %s);
        """, (user_id,))

        cur.execute("""
            DELETE FROM Assignments
            WHERE upload_id IN (SELECT upload_id FROM Uploads WHERE user_id = %s);
        """, (user_id,))

        # Insert new upload record
        cur.execute("""
            INSERT INTO Uploads (user_id, file_name, is_active)
            VALUES (%s, %s, TRUE)
            RETURNING upload_id;
        """, (user_id, file.filename))
        upload_id = cur.fetchone()[0]

        grouped = df.groupby("Employee Name")

        for name, group in grouped:
            first = group.iloc[0]

            # Parse skills
            skills_raw = str(first.get("Skill Set", "")).strip()
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else []
            skills_json = json.dumps(skills)

            # Insert employee
            cur.execute("""
                INSERT INTO Employees (upload_id, name, role, department, experience_years, skills)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING employee_id;
            """, (
                upload_id,
                name,
                first["Role"],
                first["Department"],
                float(first["Experience (Years)"]),
                skills_json
            ))
            employee_id = cur.fetchone()[0]

            # Insert assignments
            for _, row in group.iterrows():
                title = str(row.get("Current Project", "")).strip()
                if not title or title.lower() in ["none", "nan", "-", "—"]:
                    continue

                start_date = pd.to_datetime(row.get("Start Date"), errors="coerce")
                end_date = pd.to_datetime(row.get("End Date"), errors="coerce")

                if pd.isna(start_date) or pd.isna(end_date):
                    continue

                total_hours = float(row.get("Total Hours", 0) or 0)
                remaining_hours = float(row.get("Remaining Hours", 0) or 0)
                priority = str(row.get("Priority", "")).strip() or None

                cur.execute("""
                    INSERT INTO Assignments (
                        employee_id, upload_id, title, start_date, end_date,
                        total_hours, remaining_hours, priority
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    employee_id, upload_id, title,
                    start_date.date(), end_date.date(),
                    total_hours, remaining_hours, priority
                ))

        conn.commit()

        return {
            "message": "File uploaded successfully.",
            "rows": len(df)
        }

    except Exception as exc:
        conn.rollback()
        raise HTTPException(500, f"Error saving data: {exc}")
    finally:
        cur.close()
        conn.close()
