from typing import Optional

from fastapi import HTTPException

from db import get_connection
from processing.settings.weight_defaults import (
    FIXED_SEMANTIC_WEIGHT,
    NON_SEMANTIC_WEIGHT_KEYS,
    resolve_effective_weight_map,
    weight_config,
)
from utils.auth_utils import (
    PASSWORD_RULE_MESSAGE,
    hash_password,
    password_matches,
    validate_password_complexity,
)


# ----------------------------------------------------------
# fetch user settings (profile + ui preferences)
# ----------------------------------------------------------
# joins the users table with usersettings to return:
#   - name, email, created_at
#   - ui theme (default: light)
#   - font size (default: medium)
def fetch_user_settings(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT u.name, u.email, u.created_at,
                   COALESCE(s.theme, 'light'),
                   COALESCE(s.font_size, 'medium'),
                   COALESCE(s.use_custom_weights, FALSE),
                   s.weight_semantic,
                   s.weight_skill,
                   s.weight_possible_skill,
                   s.weight_soft_skill,
                   s.weight_possible_soft_skill,
                   s.weight_experience,
                   s.weight_role,
                   s.weight_availability,
                   s.weight_fairness,
                   s.weight_preferences,
                   s.weight_feedback
            FROM "Users" u
            LEFT JOIN "UserSettings" s ON u.user_id = s.user_id
            WHERE u.user_id = %s;
        """, (user_id,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "user not found")

        effective_weights = resolve_effective_weight_map({
            "semantic": row[6],
            "skill": row[7],
            "possible_skill": row[8],
            "soft_skill": row[9],
            "possible_soft_skill": row[10],
            "experience": row[11],
            "role": row[12],
            "availability": row[13],
            "fairness": row[14],
            "preferences": row[15],
            "feedback": row[16],
        })

        return {
            "name": row[0],
            "email": row[1],
            "member_since": row[2],
            "theme": row[3],
            "font_size": row[4],
            "use_custom_weights": bool(row[5]),
            "weights": effective_weights,
            "weight_config": weight_config(),
        }

    finally:
        cur.close()
        conn.close()


def _normalise_weights(weights: dict):
    # backend re-checks weights so invalid custom values are never silently saved
    if not isinstance(weights, dict):
        return None
    clean = {}
    for key in NON_SEMANTIC_WEIGHT_KEYS:
        value = weights.get(key)
        if value is None or value == "":
            if key in ("soft_skill", "possible_soft_skill"):
                clean[key] = 0.0
                continue
            return None
        try:
            num = float(value)
        except Exception:
            return None
        if num < 0:
            return None
        clean[key] = num
    total_other = sum(clean.values())
    if total_other <= 0:
        return None
    if FIXED_SEMANTIC_WEIGHT >= 1:
        return None
    # keep semantic fixed, then scale the rest to fill the remaining budget
    scaled = {
        key: round((clean[key] / total_other) * (1 - FIXED_SEMANTIC_WEIGHT), 6)
        for key in clean
    }
    scaled["semantic"] = FIXED_SEMANTIC_WEIGHT
    return scaled


def _validate_user_exists(cur, user_id: int):
    cur.execute('SELECT 1 FROM "Users" WHERE user_id = %s;', (user_id,))
    if not cur.fetchone():
        raise HTTPException(404, "user not found.")


def persist_user_settings(
    user_id: int,
    theme: Optional[str],
    font_size: Optional[str],
    use_custom_weights: Optional[bool] = None,
    weights: Optional[dict] = None,
):
    normalized = None
    if weights is not None:
        # custom weights are optional, but if supplied they must be valid
        normalized = _normalise_weights(weights)
        if normalized is None:
            raise HTTPException(400, "Invalid weights supplied.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        _validate_user_exists(cur, user_id)

        # ensure settings row exists
        cur.execute("""
            INSERT INTO "UserSettings" (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING;
        """, (user_id,))

        # update provided fields, keep previous values if null
        cur.execute("""
            UPDATE "UserSettings"
            SET theme = COALESCE(%s, theme),
                font_size = COALESCE(%s, font_size),
                use_custom_weights = COALESCE(%s, use_custom_weights),
                weight_semantic = COALESCE(%s, weight_semantic),
                weight_skill = COALESCE(%s, weight_skill),
                weight_possible_skill = COALESCE(%s, weight_possible_skill),
                weight_soft_skill = COALESCE(%s, weight_soft_skill),
                weight_possible_soft_skill = COALESCE(%s, weight_possible_soft_skill),
                weight_experience = COALESCE(%s, weight_experience),
                weight_role = COALESCE(%s, weight_role),
                weight_availability = COALESCE(%s, weight_availability),
                weight_fairness = COALESCE(%s, weight_fairness),
                weight_preferences = COALESCE(%s, weight_preferences),
                weight_feedback = COALESCE(%s, weight_feedback)
            WHERE user_id = %s;
        """, (
            theme,
            font_size,
            use_custom_weights,
            normalized.get("semantic") if normalized else None,
            normalized.get("skill") if normalized else None,
            normalized.get("possible_skill") if normalized else None,
            normalized.get("soft_skill") if normalized else None,
            normalized.get("possible_soft_skill") if normalized else None,
            normalized.get("experience") if normalized else None,
            normalized.get("role") if normalized else None,
            normalized.get("availability") if normalized else None,
            normalized.get("fairness") if normalized else None,
            normalized.get("preferences") if normalized else None,
            normalized.get("feedback") if normalized else None,
            user_id,
        ))

        conn.commit()

    finally:
        cur.close()
        conn.close()

    return {"message": "Settings updated"}


# ----------------------------------------------------------
# update user general account details (name + email)
# ----------------------------------------------------------
# validates:
#   - user exists
#   - new email is not used by another user
def update_account_details(user_id: int, name: Optional[str], email: Optional[str]):
    clean_name = name.strip() if isinstance(name, str) else name
    clean_email = email.strip().lower() if isinstance(email, str) else email
    if clean_name is not None and not clean_name:
        raise HTTPException(400, "name cannot be blank.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # ensure user exists
        cur.execute('SELECT user_id FROM "Users" WHERE user_id = %s;', (user_id,))
        if not cur.fetchone():
            raise HTTPException(404, "user not found.")

        # check email uniqueness (if provided)
        if clean_email:
            cur.execute(
                'SELECT user_id FROM "Users" WHERE email = %s AND user_id <> %s;',
                (clean_email, user_id),
            )
            if cur.fetchone():
                raise HTTPException(400, "email already in use by another account.")

        # update and return updated profile info
        cur.execute("""
            UPDATE "Users"
            SET
                name = COALESCE(%s, name),
                email = COALESCE(%s, email)
            WHERE user_id = %s
            RETURNING name, email, created_at;
        """, (clean_name, clean_email, user_id))

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


# ----------------------------------------------------------
# verify user password
# ----------------------------------------------------------
# checks:
#   - user exists
#   - provided current_password hashes to stored hash
def verify_user_password(user_id: int, current_password: str):
    if not current_password:
        raise HTTPException(400, "current password is required.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT password_hash FROM "Users" WHERE user_id = %s;', (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "user not found.")

        stored_hash = row[0]
        if not password_matches(current_password, stored_hash):
            raise HTTPException(401, "current password is incorrect.")

        return {"message": "Password verified."}

    finally:
        cur.close()
        conn.close()


# ----------------------------------------------------------
# change user password
# ----------------------------------------------------------
# validations:
#   - new password meets basic complexity rules
#   - new password differs from old one
#   - current password matches stored hash
def change_user_password(user_id: int, current_password: str, new_password: str):
    if not current_password:
        raise HTTPException(400, "current password is required.")

    # simple complexity rule: must contain uppercase + special char
    try:
        validate_password_complexity(new_password)
    except ValueError:
        raise HTTPException(400, PASSWORD_RULE_MESSAGE)

    # reject identical passwords
    if new_password.strip() == current_password.strip():
        raise HTTPException(400, "new password must be different from the current password.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        # fetch existing password hash
        cur.execute('SELECT password_hash FROM "Users" WHERE user_id = %s;', (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "user not found.")

        stored_hash = row[0]
        if not password_matches(current_password, stored_hash):
            raise HTTPException(401, "current password is incorrect.")

        # store new password hash
        new_hash = hash_password(new_password)
        cur.execute(
            'UPDATE "Users" SET password_hash = %s WHERE user_id = %s;',
            (new_hash, user_id),
        )

        conn.commit()
        return {"message": "Password updated successfully."}

    finally:
        cur.close()
        conn.close()
