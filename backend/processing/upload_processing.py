from io import BytesIO
from pathlib import Path
import json

import pandas as pd

from db import get_connection


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


class UploadProcessingError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _validate_extension(filename: str):
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UploadProcessingError(400, "Only Excel files (.xlsx or .xls) are allowed.")


def _read_dataframe(file_bytes: bytes):
    try:
        return pd.read_excel(BytesIO(file_bytes), sheet_name=0)
    except Exception as exc:
        raise UploadProcessingError(400, f"Could not read file: {exc}")


def _validate_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise UploadProcessingError(400, f"Missing required columns: {', '.join(missing)}")


def _insert_upload(cur, user_id: int, filename: str) -> int:
    cur.execute(
        """
        UPDATE Uploads
        SET is_active = FALSE
        WHERE user_id = %s;
        """,
        (user_id,),
    )

    cur.execute(
        """
        INSERT INTO Uploads (user_id, file_name, is_active)
        VALUES (%s, %s, TRUE)
        RETURNING upload_id;
        """,
        (user_id, filename),
    )

    return cur.fetchone()[0]


def _insert_employee(cur, upload_id: int, group_name: str, row: pd.Series) -> int:
    raw = str(row.get("Skill Set", "")).strip()
    skills = [s.strip() for s in raw.split(",") if s.strip()]
    skills_json = json.dumps(skills)

    cur.execute(
        """
        INSERT INTO Employees (upload_id, name, role, department, experience_years, skills)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING employee_id;
        """,
        (
            upload_id,
            group_name,
            row["Role"],
            row["Department"],
            float(row["Experience (Years)"] or 0),
            skills_json,
        ),
    )

    return cur.fetchone()[0]


def _insert_assignments(cur, upload_id: int, employee_id: int, group: pd.DataFrame):
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

        cur.execute(
            """
            INSERT INTO Assignments (
                employee_id, upload_id, title, start_date, end_date,
                total_hours, remaining_hours, priority
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                employee_id,
                upload_id,
                title,
                start_date.date(),
                end_date.date(),
                total_hours,
                remaining_hours,
                priority,
            ),
        )


def process_upload(user_id: int, filename: str, file_bytes: bytes) -> dict:
    _validate_extension(filename)
    df = _read_dataframe(file_bytes)
    _validate_columns(df)

    conn = get_connection()
    cur = conn.cursor()

    try:
        upload_id = _insert_upload(cur, user_id, filename)

        grouped = df.groupby("Employee Name")
        for name, group in grouped:
            first = group.iloc[0]
            employee_id = _insert_employee(cur, upload_id, name, first)
            _insert_assignments(cur, upload_id, employee_id, group)

        conn.commit()
        return {
            "message": "File uploaded successfully.",
            "upload_id": upload_id,
            "row_count": len(df),
        }
    except UploadProcessingError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise UploadProcessingError(500, f"Error saving data: {exc}")
    finally:
        cur.close()
        conn.close()
