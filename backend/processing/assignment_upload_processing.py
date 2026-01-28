from io import BytesIO
from pathlib import Path
import json

import pandas as pd

from db import get_connection


REQUIRED_FIELDS = [
    "title",
    "start_date",
    "end_date",
]

DEFAULT_COLUMN_MAP = {
    "employee_id": "Employee ID",
    "title": "Task Title",
    "start_date": "Start Date",
    "end_date": "End Date",
    "total_hours": "Total Hours",
    "remaining_hours": "Remaining Hours",
    "priority": "Priority",
}

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


class AssignmentUploadError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _validate_extension(filename: str):
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise AssignmentUploadError(400, "only excel files (.xlsx or .xls) are allowed.")


def _read_dataframe(file_bytes: bytes):
    try:
        return pd.read_excel(BytesIO(file_bytes), sheet_name=0)
    except Exception as exc:
        raise AssignmentUploadError(400, f"could not read file: {exc}")


def _parse_column_map(raw: str):
    if not raw:
        return DEFAULT_COLUMN_MAP
    try:
        parsed = json.loads(raw)
    except Exception:
        raise AssignmentUploadError(400, "column_map must be valid JSON.")
    if not isinstance(parsed, dict):
        raise AssignmentUploadError(400, "column_map must be a JSON object.")
    return parsed


def _validate_column_map(df: pd.DataFrame, column_map: dict):
    missing_required = [f for f in REQUIRED_FIELDS if f not in column_map]
    if missing_required:
        raise AssignmentUploadError(
            400,
            f"column_map missing required fields: {', '.join(missing_required)}",
        )

    for key, col in column_map.items():
        if col and col not in df.columns and key in REQUIRED_FIELDS:
            raise AssignmentUploadError(
                400,
                f"missing required column: {col}",
            )

    employee_id_col = column_map.get("employee_id")
    if employee_id_col is None or employee_id_col not in df.columns:
        raise AssignmentUploadError(400, "employee_id column is required.")


def _normalize_rows(df: pd.DataFrame, column_map: dict):
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "employee_id": row.get(column_map.get("employee_id")),
            "title": str(row.get(column_map["title"], "")).strip(),
            "start_date": row.get(column_map["start_date"]),
            "end_date": row.get(column_map["end_date"]),
            "total_hours": row.get(column_map.get("total_hours")),
            "remaining_hours": row.get(column_map.get("remaining_hours")),
            "priority": str(row.get(column_map.get("priority"), "")).strip() or None,
        })
    return rows


def _resolve_employee_ids(cur, user_id: int):
    cur.execute(
        """
        SELECT employee_id
        FROM "Employees"
        WHERE user_id = %s;
        """,
        (user_id,),
    )
    return {int(row[0]) for row in cur.fetchall()}


def process_assignment_upload(user_id: int, filename: str, file_bytes: bytes, column_map_raw: str):
    _validate_extension(filename)
    df = _read_dataframe(file_bytes)
    column_map = _parse_column_map(column_map_raw)
    if column_map.get("title") not in df.columns and "Current Project" in df.columns:
        column_map["title"] = "Current Project"
    _validate_column_map(df, column_map)

    rows = _normalize_rows(df, column_map)
    errors = []

    conn = get_connection()
    cur = conn.cursor()

    try:
        by_id = _resolve_employee_ids(cur, user_id)

        for idx, row in enumerate(rows):
            row_number = idx + 2

            if not row["title"]:
                errors.append(f"row {row_number}: task title is required.")

            start_date = pd.to_datetime(row["start_date"], errors="coerce")
            end_date = pd.to_datetime(row["end_date"], errors="coerce")
            if pd.isna(start_date) or pd.isna(end_date):
                errors.append(f"row {row_number}: invalid start or end date.")
            elif start_date > end_date:
                errors.append(f"row {row_number}: start date is after end date.")

            employee_id = None
            if row["employee_id"] is not None and str(row["employee_id"]).strip():
                try:
                    employee_id = int(row["employee_id"])
                except Exception:
                    errors.append(f"row {row_number}: invalid employee_id.")
            else:
                errors.append(f"row {row_number}: employee_id is required.")

            if employee_id is not None and employee_id not in by_id:
                errors.append(f"row {row_number}: employee not found.")

        if errors:
            raise AssignmentUploadError(400, " ; ".join(errors[:10]))

        cur.execute(
            """
            INSERT INTO "Uploads" (user_id, file_name, upload_type)
            VALUES (%s, %s, %s)
            RETURNING upload_id;
            """,
            (user_id, filename, "assignment_import"),
        )
        upload_id = cur.fetchone()[0]

        for row in rows:
            employee_id = int(row["employee_id"])

            start_date = pd.to_datetime(row["start_date"], errors="coerce")
            end_date = pd.to_datetime(row["end_date"], errors="coerce")

            total_raw = row.get("total_hours")
            remaining_raw = row.get("remaining_hours")
            total_hours = 0.0 if pd.isna(total_raw) else float(total_raw or 0)
            remaining_hours = 0.0 if pd.isna(remaining_raw) else float(remaining_raw or 0)
            if total_hours == 0.0 and not pd.isna(start_date) and not pd.isna(end_date):
                days = (end_date.date() - start_date.date()).days + 1
                total_hours = float(days * 8)
            if remaining_hours == 0.0 and total_hours > 0:
                remaining_hours = total_hours

            cur.execute(
                """
                INSERT INTO "Assignments" (
                    user_id,
                    employee_id,
                    upload_id,
                    title,
                    start_date,
                    end_date,
                    total_hours,
                    remaining_hours,
                    priority
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    user_id,
                    employee_id,
                    upload_id,
                    row["title"],
                    start_date.date(),
                    end_date.date(),
                    total_hours,
                    remaining_hours,
                    row["priority"],
                ),
            )

        conn.commit()

        return {
            "message": "assignments imported successfully.",
            "upload_id": upload_id,
            "row_count": len(rows),
        }

    except AssignmentUploadError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise AssignmentUploadError(500, f"error saving data: {exc}")
    finally:
        cur.close()
        conn.close()
