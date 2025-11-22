# routers/auth.py

import hashlib
import re
import psycopg2

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from db import get_connection

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register_user(payload: RegisterRequest):
    conn = get_connection()
    cur = conn.cursor()

    # password rules
    if not (re.search(r"[A-Z]", payload.password) and re.search(r"[^A-Za-z0-9]", payload.password)):
        raise HTTPException(
            400,
            "Password must include at least one uppercase letter and one special character."
        )

    password_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()

    try:
        # check if email exists
        cur.execute("SELECT 1 FROM Users WHERE email = %s;", (payload.email,))
        if cur.fetchone():
            raise HTTPException(400, "Email already registered.")

        # insert user
        cur.execute("""
            INSERT INTO Users (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING user_id, created_at;
        """, (payload.name, payload.email, password_hash))

        user_id, created_at = cur.fetchone()
        conn.commit()

        return {
            "user_id": user_id,
            "name": payload.name,
            "email": payload.email,
            "created_at": created_at.isoformat(),
            "message": "User registered successfully."
        }

    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(400, "Email already registered.")
    finally:
        cur.close()
        conn.close()


@router.post("/login")
def login_user(payload: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT user_id, name, password_hash, created_at
            FROM Users
            WHERE email = %s;
        """, (payload.email,))
        record = cur.fetchone()

        if not record:
            raise HTTPException(401, "Invalid email or password.")

        user_id, name, stored_hash, created_at = record
        given_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()

        if stored_hash != given_hash:
            raise HTTPException(401, "Invalid email or password.")

        cur.execute(
            """
            SELECT upload_id, is_active
            FROM Uploads
            WHERE user_id = %s
            ORDER BY upload_date DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        upload_row = cur.fetchone()
        active_upload_id = upload_row[0] if upload_row else None
        has_upload = bool(upload_row)

        return {
            "user_id": user_id,
            "name": name,
            "email": payload.email,
            "created_at": created_at.isoformat(),
            "has_upload": has_upload,
            "active_upload_id": active_upload_id,
            "message": "Login successful."
        }

    finally:
        cur.close()
        conn.close()
