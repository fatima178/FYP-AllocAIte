import hashlib
import re

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from db import get_connection, init_db
from routers import upload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
app.include_router(upload.router, prefix="/api")


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.get("/")
def home():
    return {"message": "Backend connected to PostgreSQL"}


@app.post("/register")
def register_user(payload: RegisterRequest):
    conn = get_connection()
    cur = conn.cursor()

    if not (re.search(r"[A-Z]", payload.password) and re.search(r"[^A-Za-z0-9]", payload.password)):
        raise HTTPException(
            status_code=400,
            detail="Password must include at least one uppercase letter and one special character.",
        )

    password_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()

    try:
        cur.execute(
            """
            SELECT 1
            FROM Users
            WHERE email = %s;
            """,
            (payload.email,),
        )
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered.")

        cur.execute(
            """
            INSERT INTO Users (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING user_id;
            """,
            (payload.name, payload.email, password_hash),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Email already registered.")
    finally:
        cur.close()
        conn.close()

    return {"user_id": user_id, "message": "User registered successfully."}


@app.post("/login")
def login_user(payload: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT user_id, password_hash
            FROM Users
            WHERE email = %s;
            """,
            (payload.email,),
        )
        record = cur.fetchone()

        if record is None:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        user_id, stored_hash = record
        payload_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()

        if stored_hash != payload_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        return {
            "user_id": user_id,
            "message": "Login successful.",
        }
    finally:
        cur.close()
        conn.close()
