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
            RETURNING user_id;
        """, (payload.name, payload.email, password_hash))

        user_id = cur.fetchone()[0]
        conn.commit()

        return {"user_id": user_id, "message": "User registered successfully."}

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
            SELECT user_id, password_hash
            FROM Users
            WHERE email = %s;
        """, (payload.email,))
        record = cur.fetchone()

        if not record:
            raise HTTPException(401, "Invalid email or password.")

        user_id, stored_hash = record
        given_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()

        if stored_hash != given_hash:
            raise HTTPException(401, "Invalid email or password.")

        return {"user_id": user_id, "message": "Login successful."}

    finally:
        cur.close()
        conn.close()
