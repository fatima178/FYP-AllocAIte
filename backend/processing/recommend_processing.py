from typing import Optional

from db import get_connection
from processing.nlp.task_matching import match_employees


# ----------------------------------------------------------
# custom exception for recommendation-related problems
# ----------------------------------------------------------
# carries an http like status code + message so the api layer
# can cleanly return structured errors to the frontend.
class RecommendationError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# ----------------------------------------------------------
# resolve which upload_id should be used
# ----------------------------------------------------------
# logic:
#   - if upload_id explicitly provided:
#       - if user_id given - validate ownership
#       - if no user_id - trust the provided id
#   - if no upload_id provided:
#       - pick latest active upload for the user
#       - fallback to the most recent upload if none active
#   - if none exist - return none
def resolve_upload_id(user_id: Optional[int], upload_id: Optional[int]) -> Optional[int]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        # caller explicitly provided an upload id
        if upload_id is not None:
            if user_id is None:
                # no user to validate against - accept directly
                return upload_id

            # check if the upload actually belongs to this user
            cur.execute(
                """
                SELECT upload_id
                FROM "Uploads"
                WHERE upload_id = %s AND user_id = %s;
                """,
                (upload_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                # user tried to access upload that isn't theirs
                raise RecommendationError(404, "upload not found for this user")
            return row[0]

        # no upload id specified, check by user context
        if user_id is None:
            # without user or upload, there's nothing to resolve
            return None

        # try active upload for the user first
        cur.execute(
            """
            SELECT upload_id
            FROM "Uploads"
            WHERE user_id = %s AND is_active = true
            ORDER BY upload_date DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        # fallback: the latest upload regardless of active flag
        cur.execute(
            """
            SELECT upload_id
            FROM "Uploads"
            WHERE user_id = %s
            ORDER BY upload_date DESC
            LIMIT 1;
            """,
            (user_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None

    finally:
        # always close db resources
        cur.close()
        conn.close()


# ----------------------------------------------------------
# generate employee recommendations for a task
# ----------------------------------------------------------
# this:
#   1) resolves correct upload dataset
#   2) validates there's usable data for the given user
#   3) runs the full ranking pipeline from match_employees()
def generate_recommendations(
    task_description: str,
    start_date: str,
    end_date: str,
    user_id: Optional[int],
    upload_id: Optional[int],
):
    if user_id is None:
        raise RecommendationError(400, "user_id is required")

    # run the matching engine and return ranking results
    return match_employees(task_description, user_id, start_date, end_date)
