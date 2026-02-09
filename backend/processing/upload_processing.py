from io import BytesIO
from pathlib import Path

import pandas as pd

from db import get_connection


# required structure for uploaded excel files
REQUIRED_COLUMNS = [
    "Employee Name",
    "Role",
    "Department",
    "Skill Set",
    "Skill Experience (Years)",
    "Skill Level (1–5)",
    "Current Project",
    "Start Date",
    "End Date",
    "Total Hours",
    "Remaining Hours",
    "Priority",
]

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


# custom error for file upload problems
class UploadProcessingError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# validate file extension
# ensures the uploaded file is an excel file.
def _validate_extension(filename: str):
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UploadProcessingError(400, "only excel files (.xlsx or .xls) are allowed.")


# read excel file into dataframe
# uses pandas to read the first sheet.
def _read_dataframe(file_bytes: bytes):
    try:
        return pd.read_excel(BytesIO(file_bytes), sheet_name=0)
    except Exception as exc:
        raise UploadProcessingError(400, f"could not read file: {exc}")


# check dataframe column structure
# verifies all required headers exist before inserting any data.
def _validate_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise UploadProcessingError(400, f"missing required columns: {', '.join(missing)}")


# insert upload entry + deactivate old uploads
# marks all previous uploads inactive and inserts a new active upload.
def _insert_upload(cur, user_id: int, filename: str) -> int:
    # deactivate older uploads
    cur.execute(
        """
        UPDATE "Uploads"
        SET is_active = FALSE
        WHERE user_id = %s;
        """,
        (user_id,),
    )

    # insert new upload and set it as active
    cur.execute(
        """
        INSERT INTO "Uploads" (user_id, file_name, is_active)
        VALUES (%s, %s, TRUE)
        RETURNING upload_id;
        """,
        (user_id, filename),
    )

    return cur.fetchone()[0]


# ----------------------------------------------------------
# insert a single employee row
# ----------------------------------------------------------
# converts "skill set" column (comma-separated) into json list
# and stores basic metadata for that employee.
def _insert_employee(cur, upload_id: int, group_name: str, row: pd.Series) -> int:
    raw_skills = str(row.get("Skill Set", "")).strip()
    raw_years = str(row.get("Skill Experience (Years)", "")).strip()
    skills = [s.strip() for s in raw_skills.split(",") if s.strip()]
    years = [s.strip() for s in raw_years.split(",") if s.strip()]

    if len(skills) != len(years):
        raise UploadProcessingError(400, "skills and experience counts must match.")

    cur.execute(
        """
        INSERT INTO "Employees" (upload_id, name, role, department)
        VALUES (%s, %s, %s, %s)
        RETURNING employee_id;
        """,
        (
            upload_id,
            group_name,                   # employee name
            row["Role"],
            row["Department"],
        ),
    )

    employee_id = cur.fetchone()[0]
    for skill, exp in zip(skills, years):
        cur.execute(
            """
            INSERT INTO "EmployeeSkills" (employee_id, skill_name, years_experience)
            VALUES (%s, %s, %s);
            """,
            (employee_id, skill, float(exp)),
        )

    return employee_id


# ----------------------------------------------------------
# insert assignments for an employee
# ----------------------------------------------------------
# each row in the employee’s group may contain a current project.
# invalid or empty project rows are skipped.
def _insert_assignments(cur, upload_id: int, employee_id: int, group: pd.DataFrame):
    for _, row in group.iterrows():
        title = str(row.get("Current Project", "")).strip()

        # skip blank or placeholder project entries
        if not title or title.lower() in ["none", "nan", "-", "—"]:
            continue

        # safely parse dates
        start_date = pd.to_datetime(row.get("Start Date"), errors="coerce")
        end_date = pd.to_datetime(row.get("End Date"), errors="coerce")

        if pd.isna(start_date) or pd.isna(end_date):
            continue

        total_hours = float(row.get("Total Hours", 0) or 0)
        remaining_hours = float(row.get("Remaining Hours", 0) or 0)
        priority = str(row.get("Priority", "")).strip() or None

        # insert assignment entry
        cur.execute(
        """
            INSERT INTO "Assignments" (
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


# ----------------------------------------------------------
# main upload processing function
# ----------------------------------------------------------
# flow:
#   1) validate excel extension
#   2) load dataframe
#   3) validate required columns
#   4) deactivate previous uploads + insert new upload entry
#   5) group rows by employee and insert employees + assignments
#   6) commit or rollback on error
def process_upload(user_id: int, filename: str, file_bytes: bytes) -> dict:
    # basic validation
    _validate_extension(filename)
    df = _read_dataframe(file_bytes)
    _validate_columns(df)

    conn = get_connection()
    cur = conn.cursor()

    try:
        upload_id = _insert_upload(cur, user_id, filename)

        # group dataframe by employee name → each group contains assignment rows
        grouped = df.groupby("Employee Name")

        for name, group in grouped:
            first = group.iloc[0]
            employee_id = _insert_employee(cur, upload_id, name, first)
            _insert_assignments(cur, upload_id, employee_id, group)

        conn.commit()

        return {
            "message": "file uploaded successfully.",
            "upload_id": upload_id,
            "row_count": len(df),
        }

    except UploadProcessingError:
        conn.rollback()
        raise

    except Exception as exc:
        conn.rollback()
        raise UploadProcessingError(500, f"error saving data: {exc}")

    finally:
        cur.close()
        conn.close()
