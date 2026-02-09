from io import BytesIO
from pathlib import Path

import pandas as pd

from db import get_connection


REQUIRED_FIELDS = [
    "name",
    "role",
    "department",
    "skills",
    "skill_experience",
]

DEFAULT_COLUMN_MAP = {
    "name": "Employee Name",
    "role": "Role",
    "department": "Department",
    "skills": "Skill Set",
    "skill_experience": "Skill Experience (Years)",
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

def _parse_skill_experience(raw):
    raw = str(raw or "").strip()
    return [s.strip() for s in raw.split(",") if s.strip()]


def _normalize_row(row, column_map: dict):
    record = {}
    record["name"] = str(row.get(column_map["name"], "")).strip()
    record["role"] = str(row.get(column_map["role"], "")).strip()
    record["department"] = str(row.get(column_map["department"], "")).strip()
    record["skills"] = _parse_skills(row.get(column_map["skills"], ""))
    record["skill_experience"] = _parse_skill_experience(
        row.get(column_map["skill_experience"], "")
    )
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
        if not record["skills"]:
            errors.append(f"row {row_number}: skills are required.")
        if not record["skill_experience"]:
            errors.append(f"row {row_number}: skill experience is required.")
        if record["skills"] and record["skill_experience"]:
            if len(record["skills"]) != len(record["skill_experience"]):
                errors.append(f"row {row_number}: skills and experience counts must match.")
            else:
                for value in record["skill_experience"]:
                    try:
                        float(value)
                    except Exception:
                        errors.append(f"row {row_number}: invalid skill experience value.")
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
            preview_rows = []
            for record in records[:10]:
                preview_rows.append({
                    "name": record["name"],
                    "role": record["role"],
                    "department": record["department"],
                    "skills": [
                        {"skill_name": s, "years_experience": float(y)}
                        for s, y in zip(record["skills"], record["skill_experience"])
                    ],
                })
            return {
                "row_count": len(records),
                "preview": preview_rows,
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
                    department
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING employee_id;
                """,
                (
                    user_id,
                    upload_id,
                    record["name"],
                    record["role"],
                    record["department"],
                ),
            )
            employee_id = cur.fetchone()[0]
            for skill, years in zip(record["skills"], record["skill_experience"]):
                cur.execute(
                    """
                    INSERT INTO "EmployeeSkills" (employee_id, skill_name, years_experience)
                    VALUES (%s, %s, %s);
                    """,
                    (employee_id, skill, float(years)),
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
