from datetime import date
from typing import Iterable, Optional

from db import get_connection


# small custom error so routers can return the right HTTP status code
class RecommendationLogError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


ALLOWED_RATINGS = {"Excellent", "Good", "Average", "Poor"}

# only these tags are accepted so feedback stays consistent for reports
ALLOWED_OUTCOME_TAGS = {
    "Delivered on time",
    "High quality",
    "Needed support",
    "Exceeded expectations",
    "Communication issues",
    "Scope changed",
}


def _serialise_outcome_tags(outcome_tags: Optional[Iterable[str]]) -> Optional[str]:
    # store multiple outcome tags as one string in the database
    if outcome_tags is None:
        return None
    clean = []
    seen = set()
    for item in outcome_tags:
        label = str(item or "").strip()
        if not label:
            continue
        if label not in ALLOWED_OUTCOME_TAGS:
            raise RecommendationLogError(400, "invalid outcome tag")
        if label in seen:
            continue
        seen.add(label)
        clean.append(label)
    return " | ".join(clean) if clean else None


def _parse_outcome_tags(raw_value: Optional[str]):
    # convert the stored string back into a list for the frontend
    text = str(raw_value or "").strip()
    if not text:
        return []
    return [part.strip() for part in text.split("|") if part.strip()]


def _assert_task_owner(cur, user_id: int, task_id: int) -> None:
    # stops one manager from editing another manager's recommendation history
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


def create_recommendation_task(
    user_id: int,
    task_description: str,
    start_date: date,
    end_date: date,
) -> int:
    # create the parent recommendation task before saving the ranked employees
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
    # save the full ranked list so later feedback can refer back to it
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
    # mark which recommended employee the manager actually chose
    conn = get_connection()
    cur = conn.cursor()
    try:
        _assert_task_owner(cur, user_id, task_id)

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
    # links the saved recommendation request to the assignment that was created
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
    outcome_tags: Optional[Iterable[str]] = None,
) -> None:
    # feedback is only allowed on the selected recommendation for this task
    if rating not in ALLOWED_RATINGS:
        raise RecommendationLogError(400, "invalid performance rating")
    serialized_outcomes = _serialise_outcome_tags(outcome_tags)

    conn = get_connection()
    cur = conn.cursor()
    try:
        _assert_task_owner(cur, user_id, task_id)

        cur.execute(
            """
            UPDATE "RecommendationLog"
            SET performance_rating = %s,
                feedback_notes = %s,
                outcome_tags = %s,
                feedback_at = CURRENT_TIMESTAMP
            WHERE task_id = %s
              AND employee_id = %s
              AND manager_selected = TRUE;
            """,
            (rating, feedback_notes, serialized_outcomes, task_id, employee_id),
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


def clear_recommendation_feedback(
    user_id: int,
    task_id: int,
    employee_id: int,
) -> None:
    # remove feedback without deleting the recommendation history row itself
    conn = get_connection()
    cur = conn.cursor()
    try:
        _assert_task_owner(cur, user_id, task_id)

        cur.execute(
            """
            UPDATE "RecommendationLog"
            SET performance_rating = NULL,
                feedback_notes = NULL,
                outcome_tags = NULL,
                feedback_at = NULL
            WHERE task_id = %s
              AND employee_id = %s
              AND manager_selected = TRUE;
            """,
            (task_id, employee_id),
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


def fetch_recommendation_history(user_id: int, limit: int = 10, offset: int = 0):
    # clamp pagination values so the history page cannot request too much at once
    safe_limit = max(1, min(int(limit), 50))
    safe_offset = max(0, int(offset))
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM "RecommendationTasks"
            WHERE user_id = %s;
            """,
            (user_id,),
        )
        total_count = int(cur.fetchone()[0] or 0)

        # fetch the history rows and the manager's selected employee if one exists
        cur.execute(
            """
            SELECT
                rt.task_id,
                rt.task_description,
                rt.start_date,
                rt.end_date,
                rt.created_at,
                rt.assignment_id,
                a.title,
                rl.employee_id,
                e.name,
                rl.performance_rating,
                rl.feedback_notes,
                rl.outcome_tags,
                rl.feedback_at
            FROM "RecommendationTasks" rt
            LEFT JOIN "Assignments" a ON a.assignment_id = rt.assignment_id
            LEFT JOIN "RecommendationLog" rl
              ON rl.task_id = rt.task_id AND rl.manager_selected = TRUE
            LEFT JOIN "Employees" e ON e.employee_id = rl.employee_id
            WHERE rt.user_id = %s
            ORDER BY rt.created_at DESC
            LIMIT %s
            OFFSET %s;
            """,
            (user_id, safe_limit, safe_offset),
        )
        rows = cur.fetchall()
        task_ids = [row[0] for row in rows]
        top_candidates_by_task = {task_id: [] for task_id in task_ids}

        if task_ids:
            # show the top few candidates so the manager can remember what was suggested
            cur.execute(
                """
                SELECT task_id, recommendation_rank, recommendation_score, employee_id, employee_name
                FROM (
                    SELECT
                        rl.task_id,
                        rl.recommendation_rank,
                        rl.recommendation_score,
                        e.employee_id,
                        e.name AS employee_name,
                        ROW_NUMBER() OVER (
                            PARTITION BY rl.task_id
                            ORDER BY rl.recommendation_rank ASC
                        ) AS position_in_task
                    FROM "RecommendationLog" rl
                    JOIN "Employees" e ON e.employee_id = rl.employee_id
                    WHERE rl.task_id = ANY(%s)
                ) ranked
                WHERE position_in_task <= 3
                ORDER BY task_id ASC, recommendation_rank ASC;
                """,
                (task_ids,),
            )
            for task_id, rank, score, employee_id, employee_name in cur.fetchall():
                top_candidates_by_task.setdefault(task_id, []).append(
                    {
                        "rank": rank,
                        "score": float(score) if score is not None else None,
                        "employee_id": employee_id,
                        "employee_name": employee_name,
                    }
                )

        tasks = []
        for row in rows:
            task_id = row[0]
            tasks.append(
                {
                    "task_id": task_id,
                    "task_description": row[1],
                    "start_date": str(row[2]) if row[2] else None,
                    "end_date": str(row[3]) if row[3] else None,
                    "created_at": row[4].isoformat() if row[4] else None,
                    "assignment_id": row[5],
                    "assignment_title": row[6],
                    "selected_employee_id": row[7],
                    "selected_employee_name": row[8],
                    "performance_rating": row[9],
                    "feedback_notes": row[10],
                    "outcome_tags": _parse_outcome_tags(row[11]),
                    "feedback_at": row[12].isoformat() if row[12] else None,
                    "top_candidates": top_candidates_by_task.get(task_id, []),
                }
            )
        return {
            "history": tasks,
            "total": total_count,
            "limit": safe_limit,
            "offset": safe_offset,
            "has_more": safe_offset + len(tasks) < total_count,
        }
    except RecommendationLogError:
        raise
    except Exception as exc:
        raise RecommendationLogError(500, str(exc))
    finally:
        cur.close()
        conn.close()
