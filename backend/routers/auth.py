# routers/auth.py

import psycopg2

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from db import get_connection
from processing.settings.weight_defaults import default_weight_tuple
from utils.auth_utils import (
    PASSWORD_RULE_MESSAGE,
    hash_password,
    password_matches,
    validate_password_complexity,
)

router = APIRouter()


# ----------------------------------------------------------
# request models for register + login
# ----------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ----------------------------------------------------------
# register a new user
# ----------------------------------------------------------
# steps:
#   1) validate password complexity
#   2) hash password using sha256
#   3) ensure email is not already taken
#   4) insert user and return metadata
@router.post("/register")
def register_user(payload: RegisterRequest):
    clean_name = payload.name.strip()
    clean_email = payload.email.strip().lower()
    if len(clean_name.split()) < 2:
        raise HTTPException(400, "please enter your full name.")

    conn = get_connection()
    cur = conn.cursor()

    # basic password rules
    try:
        validate_password_complexity(payload.password)
    except ValueError:
        raise HTTPException(400, PASSWORD_RULE_MESSAGE)

    password_hash = hash_password(payload.password)

    try:
        # check email uniqueness before inserting
        cur.execute('SELECT 1 FROM "Users" WHERE email = %s;', (clean_email,))
        if cur.fetchone():
            raise HTTPException(400, "email already registered.")

        # insert new user
        cur.execute("""
            INSERT INTO "Users" (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING user_id, created_at;
        """, (clean_name, clean_email, password_hash))

        user_id, created_at = cur.fetchone()
        default_weights = default_weight_tuple()

        cur.execute(
            """
            INSERT INTO "UserSettings" (
                user_id,
                theme,
                font_size,
                use_custom_weights,
                weight_semantic,
                weight_skill,
                weight_possible_skill,
                weight_soft_skill,
                weight_possible_soft_skill,
                weight_experience,
                weight_role,
                weight_availability,
                weight_fairness,
                weight_preferences,
                weight_feedback
            )
            VALUES (
                %s, 'light', 'medium', FALSE,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (user_id) DO UPDATE
            SET
                theme = COALESCE("UserSettings".theme, EXCLUDED.theme),
                font_size = COALESCE("UserSettings".font_size, EXCLUDED.font_size),
                use_custom_weights = COALESCE("UserSettings".use_custom_weights, EXCLUDED.use_custom_weights),
                weight_semantic = COALESCE("UserSettings".weight_semantic, EXCLUDED.weight_semantic),
                weight_skill = COALESCE("UserSettings".weight_skill, EXCLUDED.weight_skill),
                weight_possible_skill = COALESCE("UserSettings".weight_possible_skill, EXCLUDED.weight_possible_skill),
                weight_soft_skill = COALESCE("UserSettings".weight_soft_skill, EXCLUDED.weight_soft_skill),
                weight_possible_soft_skill = COALESCE("UserSettings".weight_possible_soft_skill, EXCLUDED.weight_possible_soft_skill),
                weight_experience = COALESCE("UserSettings".weight_experience, EXCLUDED.weight_experience),
                weight_role = COALESCE("UserSettings".weight_role, EXCLUDED.weight_role),
                weight_availability = COALESCE("UserSettings".weight_availability, EXCLUDED.weight_availability),
                weight_fairness = COALESCE("UserSettings".weight_fairness, EXCLUDED.weight_fairness),
                weight_preferences = COALESCE("UserSettings".weight_preferences, EXCLUDED.weight_preferences),
                weight_feedback = COALESCE("UserSettings".weight_feedback, EXCLUDED.weight_feedback);
            """,
            (user_id, *default_weights),
        )
        conn.commit()

        return {
            "user_id": user_id,
            "name": clean_name,
            "email": clean_email,
            "created_at": created_at.isoformat(),
            "account_type": "manager",
            "employee_id": None,
            "message": "user registered successfully."
        }

    except psycopg2.IntegrityError:
        # db-level unique constraint fallback
        conn.rollback()
        raise HTTPException(400, "email already registered.")

    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------
# login user
# ----------------------------------------------------------
# steps:
#   1) lookup user by email
#   2) hash provided password and compare with stored hash
#   3) if valid, fetch latest upload for convenience
#   4) return login success response
@router.post("/login")
def login_user(payload: LoginRequest):
    clean_email = payload.email.strip().lower()
    conn = get_connection()
    cur = conn.cursor()

    try:
        # find account by email
        cur.execute("""
            SELECT user_id, name, password_hash, created_at, account_type, employee_id
            FROM "Users"
            WHERE email = %s;
        """, (clean_email,))
        record = cur.fetchone()

        if not record:
            raise HTTPException(401, "invalid email or password.")

        user_id, name, stored_hash, created_at, account_type, employee_id = record

        # hash incoming password
        if not password_matches(payload.password, stored_hash):
            raise HTTPException(401, "invalid email or password.")

        cur.execute(
            'SELECT 1 FROM "Employees" WHERE user_id = %s LIMIT 1;',
            (user_id,),
        )
        has_upload = bool(cur.fetchone())

        return {
            "user_id": user_id,
            "name": name,
            "email": clean_email,
            "created_at": created_at.isoformat(),
            "has_upload": has_upload,
            "account_type": account_type or "manager",
            "employee_id": employee_id,
            "message": "login successful."
        }

    finally:
        cur.close()
        conn.close()
