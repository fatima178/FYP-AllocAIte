from fastapi import APIRouter, HTTPException
from db import get_connection

router = APIRouter()

# -------------------------------------
# GET USER SETTINGS
# -------------------------------------
@router.get("/settings")
def get_settings(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT u.name, u.email, u.created_at,
               COALESCE(s.theme, 'light'),
               COALESCE(s.font_size, 'medium')
        FROM Users u
        LEFT JOIN UserSettings s ON u.user_id = s.user_id
        WHERE u.user_id = %s;
    """, (user_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(404, "User not found")

    return {
        "name": row[0],
        "email": row[1],
        "member_since": row[2],
        "theme": row[3],
        "font_size": row[4],
    }


# -------------------------------------
# UPDATE USER SETTINGS
# -------------------------------------
@router.post("/settings")
def update_settings(data: dict):
    user_id = data.get("user_id")
    theme = data.get("theme")
    font_size = data.get("font_size")

    if not user_id:
        raise HTTPException(400, "user_id is required")

    conn = get_connection()
    cur = conn.cursor()

    # Ensure row exists
    cur.execute("""
        INSERT INTO UserSettings (user_id)
        VALUES (%s)
        ON CONFLICT (user_id) DO NOTHING;
    """, (user_id,))

    # Update fields
    cur.execute("""
        UPDATE UserSettings
        SET theme = COALESCE(%s, theme),
            font_size = COALESCE(%s, font_size)
        WHERE user_id = %s;
    """, (theme, font_size, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Settings updated"}
