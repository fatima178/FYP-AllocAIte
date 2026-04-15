import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict

from db import get_connection
from utils.auth_utils import hash_password, validate_password_complexity


# used when invite work fails so the router can show a clean error
class InviteProcessingError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _hash_token(token: str) -> str:
    # store only a hash of the invite token, not the raw link token
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _build_invite_link(token: str) -> str:
    # frontend base url can change between local development and deployment
    base = (os.environ.get("FRONTEND_BASE_URL") or "http://localhost:3000").rstrip("/")
    return f"{base}/invite?token={token}"


def create_invite(manager_user_id: int, employee_id: int) -> Dict[str, str]:
    # managers can create one login invite for an employee they own
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT name
            FROM "Employees"
            WHERE employee_id = %s AND user_id = %s;
            """,
            (employee_id, manager_user_id),
        )
        row = cur.fetchone()
        if not row:
            raise InviteProcessingError(404, "employee not found for this user")

        # do not create another invite if the employee already has a user account
        cur.execute(
            'SELECT 1 FROM "Users" WHERE employee_id = %s;',
            (employee_id,),
        )
        if cur.fetchone():
            raise InviteProcessingError(400, "employee already has a login")

        token = secrets.token_urlsafe(24)
        token_hash = _hash_token(token)
        expires_at = datetime.utcnow() + timedelta(days=7)

        # save the hashed token so the real token only exists in the invite link
        cur.execute(
            """
            INSERT INTO "EmployeeInvites" (
                manager_user_id,
                employee_id,
                token_hash,
                expires_at
            )
            VALUES (%s, %s, %s, %s);
            """,
            (manager_user_id, employee_id, token_hash, expires_at),
        )

        conn.commit()
        return {
            "invite_link": _build_invite_link(token),
            "employee_name": row[0],
            "expires_at": expires_at.isoformat() + "Z",
        }

    except InviteProcessingError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise InviteProcessingError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def _validate_password(password: str):
    # employee invite passwords use the same rules as manager passwords
    if not password:
        raise InviteProcessingError(400, "password is required")
    try:
        validate_password_complexity(password)
    except ValueError as exc:
        raise InviteProcessingError(400, str(exc))


def accept_invite(token: str, email: str, password: str) -> Dict[str, str]:
    # turn a valid invite link into an employee login account
    clean_token = str(token or "").strip()
    if not clean_token:
        raise InviteProcessingError(400, "invite token is required")

    clean_email = str(email or "").strip().lower()
    if not clean_email:
        raise InviteProcessingError(400, "email is required")

    _validate_password(password)

    token_hash = _hash_token(clean_token)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT invite_id, manager_user_id, employee_id, expires_at, used_at
            FROM "EmployeeInvites"
            WHERE token_hash = %s;
            """,
            (token_hash,),
        )
        row = cur.fetchone()
        if not row:
            raise InviteProcessingError(404, "invite not found")

        invite_id, manager_user_id, employee_id, expires_at, used_at = row
        if used_at is not None:
            raise InviteProcessingError(400, "invite already used")
        if expires_at and expires_at < datetime.utcnow():
            raise InviteProcessingError(400, "invite expired")

        # emails must stay unique across manager and employee accounts
        cur.execute(
            'SELECT 1 FROM "Users" WHERE email = %s;',
            (clean_email,),
        )
        if cur.fetchone():
            raise InviteProcessingError(400, "email already registered")

        cur.execute(
            'SELECT 1 FROM "Users" WHERE employee_id = %s;',
            (employee_id,),
        )
        if cur.fetchone():
            raise InviteProcessingError(400, "employee already has a login")

        cur.execute(
            'SELECT name FROM "Employees" WHERE employee_id = %s;',
            (employee_id,),
        )
        emp_row = cur.fetchone()
        if not emp_row:
            raise InviteProcessingError(404, "employee not found")
        employee_name = emp_row[0] or "Employee"

        password_hash = hash_password(password)

        # employee account is linked back to the existing employee row
        cur.execute(
            """
            INSERT INTO "Users" (name, email, password_hash, account_type, employee_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id;
            """,
            (employee_name, clean_email, password_hash, "employee", employee_id),
        )
        user_id = cur.fetchone()[0]

        cur.execute(
            'UPDATE "EmployeeInvites" SET used_at = CURRENT_TIMESTAMP WHERE invite_id = %s;',
            (invite_id,),
        )

        conn.commit()
        return {
            "user_id": user_id,
            "employee_id": employee_id,
            "manager_user_id": manager_user_id,
        }
    except InviteProcessingError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise InviteProcessingError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def get_invite_info(token: str) -> Dict[str, str]:
    # used by the frontend invite page before the employee accepts the invite
    clean_token = str(token or "").strip()
    if not clean_token:
        raise InviteProcessingError(400, "invite token is required")

    token_hash = _hash_token(clean_token)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT i.employee_id, i.expires_at, i.used_at, e.name
            FROM "EmployeeInvites" i
            JOIN "Employees" e ON i.employee_id = e.employee_id
            WHERE i.token_hash = %s;
            """,
            (token_hash,),
        )
        row = cur.fetchone()
        if not row:
            raise InviteProcessingError(404, "invite not found")

        employee_id, expires_at, used_at, name = row
        if used_at is not None:
            raise InviteProcessingError(400, "invite already used")
        if expires_at and expires_at < datetime.utcnow():
            raise InviteProcessingError(400, "invite expired")

        return {
            "employee_id": employee_id,
            "name": name or "Employee",
            "expires_at": expires_at.isoformat() + "Z" if expires_at else None,
        }
    except InviteProcessingError:
        raise
    except Exception as exc:
        raise InviteProcessingError(500, str(exc))
    finally:
        cur.close()
        conn.close()
