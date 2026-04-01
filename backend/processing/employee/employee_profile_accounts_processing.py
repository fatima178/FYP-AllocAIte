from utils.auth_utils import PASSWORD_RULE_MESSAGE, hash_password, validate_password_complexity
from db import get_connection
from processing.employee.employee_profile_common import EmployeeProfileError


def _validate_password(password: str):
    try:
        validate_password_complexity(password)
    except ValueError:
        raise EmployeeProfileError(400, PASSWORD_RULE_MESSAGE)


def create_employee_account(
    manager_user_id: int,
    employee_id: int,
    name: str,
    email: str,
    password: str,
):
    clean_name = str(name or "").strip()
    clean_email = str(email or "").strip().lower()
    if not clean_name:
        raise EmployeeProfileError(400, "name is required")
    if not clean_email:
        raise EmployeeProfileError(400, "email is required")
    _validate_password(password)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT 1
            FROM "Employees"
            WHERE employee_id = %s AND user_id = %s;
            """,
            (employee_id, manager_user_id),
        )
        if not cur.fetchone():
            raise EmployeeProfileError(404, "employee not found for this user")

        cur.execute('SELECT 1 FROM "Users" WHERE email = %s;', (clean_email,))
        if cur.fetchone():
            raise EmployeeProfileError(400, "email already registered.")

        cur.execute('SELECT 1 FROM "Users" WHERE employee_id = %s;', (employee_id,))
        if cur.fetchone():
            raise EmployeeProfileError(400, "employee already has a login")

        password_hash = hash_password(password)
        cur.execute(
            """
            INSERT INTO "Users" (name, email, password_hash, account_type, employee_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id;
            """,
            (clean_name, clean_email, password_hash, "employee", employee_id),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return {"user_id": user_id, "employee_id": employee_id}
    except EmployeeProfileError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise EmployeeProfileError(500, str(exc))
    finally:
        cur.close()
        conn.close()
