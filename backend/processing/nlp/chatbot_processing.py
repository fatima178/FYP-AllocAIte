from datetime import datetime, timedelta
from dateutil import parser
import re

from db import get_connection


def parse_date_range(text: str):
    t = text.lower().strip()
    now = datetime.today()

    if "tomorrow" in t:
        d = now + timedelta(days=1)
        return d.date(), d.date()

    if "today" in t:
        return now.date(), now.date()

    match = re.search(r"in (\d+) days", t)
    if match:
        offset = int(match.group(1))
        d = now + timedelta(days=offset)
        return d.date(), d.date()

    if "next week" in t:
        start = now + timedelta(days=(7 - now.weekday()))
        end = start + timedelta(days=6)
        return start.date(), end.date()

    if "this week" in t:
        start = now - timedelta(days=now.weekday())
        end = start + timedelta(days=6)
        return start.date(), end.date()

    if "next month" in t:
        first = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
        last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return first.date(), last.date()

    iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", t)
    if len(iso_dates) >= 1:
        try:
            start = parser.parse(iso_dates[0]).date()
            end = parser.parse(iso_dates[-1]).date()
            return start, end
        except Exception:
            pass

    try:
        d = parser.parse(t, fuzzy=True).date()
        return d, d
    except Exception:
        return None, None


def parse_skills(text: str):
    t = text.lower()
    known = [
        "python",
        "django",
        "sql",
        "nlp",
        "tensorflow",
        "api",
        "backend",
        "frontend",
        "ui",
        "ux",
        "design",
    ]
    return [s for s in known if s in t]


def parse_employee(cur, upload_id, text: str):
    t = text.lower()

    cur.execute(
        "SELECT employee_id, name FROM employees WHERE upload_id = %s;",
        (upload_id,),
    )
    rows = cur.fetchall()

    for emp_id, full_name in rows:
        full = full_name.lower()
        first = full.split(" ")[0]

        if full in t or first in t:
            return emp_id, full_name

    return None, None


def detect_intent(text: str):
    t = text.lower()

    if "available" in t or "free" in t or "busy" in t:
        return "availability"

    if "doing" in t or "working on" in t or "assigned" in t or "task" in t:
        return "assignment"

    if "skill" in t or "knows" in t or "expert" in t or "has" in t:
        return "skills"

    if "backend" in t or "developer" in t or "designer" in t or "analyst" in t:
        return "role"

    return "fallback"


def handle_availability(cur, upload_id: int, message: str):
    start, end = parse_date_range(message)
    if not start:
        return {
            "response": (
                "I couldn’t understand the timeframe. Try 'next week', 'tomorrow', "
                "or a date like 2025-02-10."
            )
        }

    cur.execute(
        """
        SELECT name FROM employees
        WHERE upload_id = %s
          AND employee_id NOT IN (
              SELECT employee_id FROM assignments
              WHERE upload_id = %s
                AND start_date <= %s
                AND end_date >= %s
          );
        """,
        (upload_id, upload_id, end, start),
    )

    names = sorted(set([r[0] for r in cur.fetchall()]))

    if not names:
        return {"response": f"No one is available between {start} and {end}."}

    return {
        "response": f"Available between {start} and {end}: " + ", ".join(names)
    }


def handle_skills(cur, upload_id: int, message: str):
    skills = parse_skills(message)
    if not skills:
        return {"response": "Specify a skill (e.g., Python, SQL, UI design)."}

    conditions = []
    params = [upload_id]
    for skill in skills:
        conditions.append("skills::text ILIKE %s")
        params.append(f"%{skill}%")

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    query = f"""
        SELECT name
        FROM employees
        WHERE upload_id = %s
          AND {where_clause};
    """
    cur.execute(query, params)

    names = sorted(set([r[0] for r in cur.fetchall()]))

    if not names:
        return {"response": "No employees found with those skills."}

    return {"response": f"Employees with {', '.join(skills)}: " + ", ".join(names)}


def handle_assignment(cur, upload_id: int, message: str):
    emp_id, full_name = parse_employee(cur, upload_id, message)
    if not emp_id:
        return {
            "response": "I couldn’t find that employee. Try full or first name."
        }

    start, end = parse_date_range(message)
    if not start:
        return {
            "response": (
                "Specify a timeframe (e.g., 'this week', 'tomorrow', or '2025-02-05')."
            )
        }

    cur.execute(
        """
        SELECT title
        FROM assignments
        WHERE employee_id = %s
          AND upload_id = %s
          AND start_date <= %s
          AND end_date >= %s;
        """,
        (emp_id, upload_id, end, start),
    )

    tasks = [r[0] for r in cur.fetchall()]

    if not tasks:
        return {"response": f"{full_name} has no tasks between {start} and {end}."}

    return {"response": f"{full_name} is working on: " + ", ".join(tasks)}


def handle_role(cur, upload_id: int):
    cur.execute(
        """
        SELECT name FROM employees
        WHERE upload_id = %s
          AND (
              LOWER(role) LIKE '%%backend%%'
              OR LOWER(role) LIKE '%%developer%%'
              OR LOWER(role) LIKE '%%designer%%'
              OR LOWER(role) LIKE '%%analyst%%'
          );
        """,
        (upload_id,),
    )
    names = sorted(set([r[0] for r in cur.fetchall()]))

    if not names:
        return {"response": "No developers found."}

    return {"response": "Developers: " + ", ".join(names)}


def resolve_upload_id(cur, user_id: int):
    cur.execute(
        """
        SELECT upload_id
        FROM uploads
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
        FROM uploads
        WHERE user_id = %s
        ORDER BY upload_date DESC
        LIMIT 1;
        """,
        (user_id,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def handle_chatbot_query(message: str, user_id: int):
    message = (message or "").strip()
    if not message:
        raise ValueError("Missing message")
    if not user_id:
        raise ValueError("Missing user_id")

    intent = detect_intent(message)
    conn = get_connection()
    cur = conn.cursor()

    try:
        upload_id = resolve_upload_id(cur, user_id)
        if not upload_id:
            return {
                "response": "No employee data found. Please upload your team sheet first."
            }

        if intent == "availability":
            return handle_availability(cur, upload_id, message)
        if intent == "skills":
            return handle_skills(cur, upload_id, message)
        if intent == "assignment":
            return handle_assignment(cur, upload_id, message)
        if intent == "role":
            return handle_role(cur, upload_id)

        return {
            "response": "I didn’t understand that. Try asking about availability, skills, roles, or assignments."
        }
    finally:
        cur.close()
        conn.close()
