from typing import Optional

from db import get_connection
from processing.nlp.task_matching import match_employees


class RecommendationError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def resolve_upload_id(user_id: Optional[int], upload_id: Optional[int]) -> Optional[int]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        if upload_id is not None:
            if user_id is None:
                return upload_id

            cur.execute(
                """
                SELECT upload_id
                FROM Uploads
                WHERE upload_id = %s AND user_id = %s;
                """,
                (upload_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                raise RecommendationError(404, "upload not found for this user")
            return row[0]

        if user_id is None:
            return None

        cur.execute(
            """
            SELECT upload_id
            FROM Uploads
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY upload_date DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute(
            """
            SELECT upload_id
            FROM Uploads
            WHERE user_id = %s
            ORDER BY upload_date DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None

    finally:
        cur.close()
        conn.close()


def generate_recommendations(
    task_description: str,
    start_date: str,
    end_date: str,
    user_id: Optional[int],
    upload_id: Optional[int],
):
    resolved_upload_id = resolve_upload_id(user_id, upload_id)
    if not resolved_upload_id:
        raise RecommendationError(400, "no uploads found for this user")

    return match_employees(task_description, resolved_upload_id, start_date, end_date)
