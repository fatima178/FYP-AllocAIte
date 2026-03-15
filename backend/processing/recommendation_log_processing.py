from datetime import date
from typing import Iterable, Optional

from db import get_connection


class RecommendationLogError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


ALLOWED_RATINGS = {"Excellent", "Good", "Average", "Poor"}


def create_recommendation_task(
    user_id: int,
    task_description: str,
    start_date: date,
    end_date: date,
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO "RecommendationTasks" (
                user_id,
                task_description,
                start_date,
                end_date
            )
            VALUES (%s, %s, %s, %s)
            RETURNING task_id;
            """,
            (user_id, task_description, start_date, end_date),
        )
        task_id = cur.fetchone()[0]
        conn.commit()
        return task_id
    except Exception as exc:
        conn.rollback()
        raise RecommendationLogError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def log_recommendations(
    task_id: int,
    recommendations: Iterable[dict],
) -> None:
    rows = []
    for idx, rec in enumerate(recommendations, start=1):
        employee_id = rec.get("employee_id")
        score = rec.get("final_score")
        rows.append((task_id, employee_id, idx, score))

    if not rows:
        return

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.executemany(
            """
            INSERT INTO "RecommendationLog" (
                task_id,
                employee_id,
                recommendation_rank,
                recommendation_score
            )
            VALUES (%s, %s, %s, %s);
            """,
            rows,
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise RecommendationLogError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def mark_manager_selected(
    user_id: int,
    task_id: int,
    employee_id: int,
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT 1
            FROM "RecommendationTasks"
            WHERE task_id = %s AND user_id = %s;
            """,
            (task_id, user_id),
        )
        if not cur.fetchone():
            raise RecommendationLogError(404, "recommendation task not found for this user")

        cur.execute(
            """
            UPDATE "RecommendationLog"
            SET manager_selected = CASE WHEN employee_id = %s THEN TRUE ELSE FALSE END
            WHERE task_id = %s;
            """,
            (employee_id, task_id),
        )

        conn.commit()
    except RecommendationLogError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise RecommendationLogError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def attach_assignment_to_task(
    user_id: int,
    task_id: int,
    assignment_id: int,
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE "RecommendationTasks"
            SET assignment_id = %s
            WHERE task_id = %s
              AND user_id = %s;
            """,
            (assignment_id, task_id, user_id),
        )
        if cur.rowcount == 0:
            raise RecommendationLogError(404, "recommendation task not found for this user")
        conn.commit()
    except RecommendationLogError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise RecommendationLogError(500, str(exc))
    finally:
        cur.close()
        conn.close()


def submit_recommendation_feedback(
    user_id: int,
    task_id: int,
    employee_id: int,
    rating: str,
    feedback_notes: Optional[str] = None,
) -> None:
    if rating not in ALLOWED_RATINGS:
        raise RecommendationLogError(400, "invalid performance rating")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT 1
            FROM "RecommendationTasks"
            WHERE task_id = %s AND user_id = %s;
            """,
            (task_id, user_id),
        )
        if not cur.fetchone():
            raise RecommendationLogError(404, "recommendation task not found for this user")

        cur.execute(
            """
            UPDATE "RecommendationLog"
            SET performance_rating = %s,
                feedback_notes = %s,
                feedback_at = CURRENT_TIMESTAMP
            WHERE task_id = %s
              AND employee_id = %s
              AND manager_selected = TRUE;
            """,
            (rating, feedback_notes, task_id, employee_id),
        )

        if cur.rowcount == 0:
            raise RecommendationLogError(404, "selected recommendation not found for this task")

        conn.commit()
    except RecommendationLogError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise RecommendationLogError(500, str(exc))
    finally:
        cur.close()
        conn.close()
