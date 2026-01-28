import json
from io import BytesIO
from pathlib import Path

import pandas as pd

from db import get_connection


REQUIRED_FIELDS = [
    "name",
    "role",
    "department",
    "skills",
    "experience_years",
]

DEFAULT_COLUMN_MAP = {
    "name": "Employee Name",
    "role": "Role",
    "department": "Department",
    "skills": "Skill Set",
    "experience_years": "Experience (Years)",
}

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


class SetupImportError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _validate_extension(filename: str):
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise SetupImportError(400, "only excel files (.xlsx or .xls) are allowed.")


def _read_dataframe(file_bytes: bytes):
    try:
        return pd.read_excel(BytesIO(file_bytes), sheet_name=0)
    except Exception as exc:
        raise SetupImportError(400, f"could not read file: {exc}")


def _parse_column_map(raw: str):
    if not raw:
        return DEFAULT_COLUMN_MAP
    try:
        parsed = json.loads(raw)
    except Exception:
        raise SetupImportError(400, "column_map must be valid JSON.")
    if not isinstance(parsed, dict):
        raise SetupImportError(400, "column_map must be a JSON object.")
    return parsed


def _validate_column_map(df: pd.DataFrame, column_map: dict):
    missing_fields = [f for f in REQUIRED_FIELDS if f not in column_map]
    if missing_fields:
        raise SetupImportError(
            400,
            f"column_map missing required fields: {', '.join(missing_fields)}",
        )

    missing_columns = [column_map[f] for f in REQUIRED_FIELDS if column_map[f] not in df.columns]
    if missing_columns:
        raise SetupImportError(
            400,
            f"missing required columns: {', '.join(missing_columns)}",
        )


def _parse_skills(raw):
    raw = str(raw or "").strip()
    return [s.strip() for s in raw.split(",") if s.strip()]


def _normalize_row(row, column_map: dict):
    record = {}
    record["name"] = str(row.get(column_map["name"], "")).strip()
    record["role"] = str(row.get(column_map["role"], "")).strip()
    record["department"] = str(row.get(column_map["department"], "")).strip()
    record["skills"] = _parse_skills(row.get(column_map["skills"], ""))
    record["experience_years"] = float(row.get(column_map["experience_years"], 0) or 0)
    return record


def _validate_records(records):
    errors = []
    for idx, record in enumerate(records):
        row_number = idx + 2
        if not record["name"]:
            errors.append(f"row {row_number}: name is required.")
        if not record["role"]:
            errors.append(f"row {row_number}: role is required.")
        if not record["department"]:
            errors.append(f"row {row_number}: department is required.")
    return errors


def _user_has_employees(cur, user_id: int) -> bool:
    cur.execute('SELECT 1 FROM "Employees" WHERE user_id = %s LIMIT 1;', (user_id,))
    return bool(cur.fetchone())


def process_employee_setup_import(
    user_id: int,
    filename: str,
    file_bytes: bytes,
    column_map_raw: str,
    preview: bool,
):
    _validate_extension(filename)
    df = _read_dataframe(file_bytes)
    column_map = _parse_column_map(column_map_raw)
    _validate_column_map(df, column_map)

    records = [_normalize_row(row, column_map) for _, row in df.iterrows()]
    errors = _validate_records(records)

    conn = get_connection()
    cur = conn.cursor()

    try:
        if _user_has_employees(cur, user_id):
            raise SetupImportError(403, "employees already exist for this user.")

        if preview:
            return {
                "row_count": len(records),
                "preview": records[:10],
                "errors": errors,
                "can_import": len(errors) == 0,
            }

        if errors:
            raise SetupImportError(400, " ; ".join(errors[:10]))

        cur.execute(
            """
            INSERT INTO "Uploads" (user_id, file_name, upload_type)
            VALUES (%s, %s, %s)
            RETURNING upload_id;
            """,
            (user_id, filename, "employee_setup"),
        )
        upload_id = cur.fetchone()[0]

        for record in records:
            cur.execute(
                """
                INSERT INTO "Employees" (
                    user_id,
                    upload_id,
                    name,
                    role,
                    department,
                    experience_years,
                    skills
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    user_id,
                    upload_id,
                    record["name"],
                    record["role"],
                    record["department"],
                    record["experience_years"],
                    json.dumps(record["skills"]),
                ),
            )

        conn.commit()

        return {
            "message": "employees imported successfully.",
            "row_count": len(records),
            "upload_id": upload_id,
        }

    except SetupImportError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise SetupImportError(500, f"error saving data: {exc}")
    finally:
        cur.close()
        conn.close()
