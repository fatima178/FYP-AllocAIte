import hashlib
import re
from typing import Optional

from fastapi import HTTPException

from db import get_connection


def fetch_user_settings(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT u.name, u.email, u.created_at,
                   COALESCE(s.theme, 'light'),
                   COALESCE(s.font_size, 'medium')
            FROM Users u
            LEFT JOIN UserSettings s ON u.user_id = s.user_id
            WHERE u.user_id = %s;
        """, (user_id,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "User not found")

        return {
            "name": row[0],
            "email": row[1],
            "member_since": row[2],
            "theme": row[3],
            "font_size": row[4],
        }
    finally:
        cur.close()
        conn.close()


def persist_user_settings(user_id: int, theme: Optional[str], font_size: Optional[str]):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO UserSettings (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING;
        """, (user_id,))

        cur.execute("""
            UPDATE UserSettings
            SET theme = COALESCE(%s, theme),
                font_size = COALESCE(%s, font_size)
            WHERE user_id = %s;
        """, (theme, font_size, user_id))

        conn.commit()
    finally:
        cur.close()
        conn.close()

    return {"message": "Settings updated"}


def update_account_details(user_id: int, name: Optional[str], email: Optional[str]):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT user_id FROM Users WHERE user_id = %s;", (user_id,))
        if not cur.fetchone():
            raise HTTPException(404, "User not found.")

        if email:
            cur.execute(
                "SELECT user_id FROM Users WHERE email = %s AND user_id <> %s;",
                (email, user_id),
            )
            if cur.fetchone():
                raise HTTPException(400, "Email already in use by another account.")

        cur.execute(
            """
            UPDATE Users
            SET
                name = COALESCE(%s, name),
                email = COALESCE(%s, email)
            WHERE user_id = %s
            RETURNING name, email, created_at;
            """,
            (name, email, user_id),
        )

        updated = cur.fetchone()
        conn.commit()

        return {
            "message": "Account details updated.",
            "name": updated[0],
            "email": updated[1],
            "member_since": updated[2],
        }
    finally:
        cur.close()
        conn.close()


def verify_user_password(user_id: int, current_password: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT password_hash FROM Users WHERE user_id = %s;", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "User not found.")

        stored_hash = row[0]
        current_hash = hashlib.sha256(current_password.encode("utf-8")).hexdigest()
        if stored_hash != current_hash:
            raise HTTPException(401, "Current password is incorrect.")

        return {"message": "Password verified."}
    finally:
        cur.close()
        conn.close()


def change_user_password(user_id: int, current_password: str, new_password: str):
    password_rules = (
        re.search(r"[A-Z]", new_password)
        and re.search(r"[^A-Za-z0-9]", new_password)
    )
    if not password_rules:
        raise HTTPException(
            400,
            "Password must include at least one uppercase letter and one special character.",
        )

    if new_password.strip() == current_password.strip():
        raise HTTPException(400, "New password must be different from the current password.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT password_hash FROM Users WHERE user_id = %s;",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "User not found.")

        stored_hash = row[0]
        current_hash = hashlib.sha256(current_password.encode("utf-8")).hexdigest()
        if stored_hash != current_hash:
            raise HTTPException(401, "Current password is incorrect.")

        new_hash = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
        cur.execute(
            "UPDATE Users SET password_hash = %s WHERE user_id = %s;",
            (new_hash, user_id),
        )
        conn.commit()
        return {"message": "Password updated successfully."}
    finally:
        cur.close()
        conn.close()
