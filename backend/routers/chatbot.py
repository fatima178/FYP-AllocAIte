from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import re
from db import get_connection

router = APIRouter(tags=["Chatbot"])


# -----------------------------------------------------
# DATE PARSER
# -----------------------------------------------------
def parse_date_range(text: str):
    t = text.lower()
    now = datetime.today()

    if "next week" in t:
        start = now + timedelta(days=(7 - now.weekday()))
        end = start + timedelta(days=6)
        return start.date(), end.date()

    if "this week" in t:
        start = now - timedelta(days=now.weekday())
        end = start + timedelta(days=6)
        return start.date(), end.date()

    dates = re.findall(r"\d{4}-\d{2}-\d{2}", t)
    if dates:
        start = datetime.strptime(dates[0], "%Y-%m-%d").date()
        end = datetime.strptime(dates[-1], "%Y-%m-%d").date()
        return start, end

    return None, None


# -----------------------------------------------------
# SKILL PARSER
# -----------------------------------------------------
def parse_skills(text: str):
    t = text.lower()
    known = ["python", "django", "sql", "nlp", "tensorflow", "api", "backend", "frontend"]
    return [s for s in known if s in t]


# -----------------------------------------------------
# EMPLOYEE NAME PARSER
# -----------------------------------------------------
def parse_employee(text: str):
    t = text.lower()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT employee_id, name FROM employees;")
    rows = cur.fetchall()

    for emp_id, full_name in rows:
        full = full_name.lower()
        first = full.split(" ")[0]

        if full in t or first in t:
            return emp_id, full_name

    return None, None


# -----------------------------------------------------
# INTENT DETECTION
# -----------------------------------------------------
def detect_intent(text: str):
    t = text.lower()

    if "available" in t or "free" in t:
        return "availability"

    if "doing" in t or "working on" in t or "assigned" in t:
        return "assignment"

    if "skill" in t or "knows" in t or "expert" in t or "has" in t:
        return "skills"

    if "backend" in t or "developer" in t:
        return "role"

    return "fallback"


# -----------------------------------------------------
# ENDPOINT
# -----------------------------------------------------
@router.post("/chatbot")
def chatbot(data: dict):
    message = data.get("message", "").strip()
    if not message:
        raise HTTPException(400, "Missing message")

    intent = detect_intent(message)

    conn = get_connection()
    cur = conn.cursor()

    # ------------------------------------
    # AVAILABILITY
    # ------------------------------------
    if intent == "availability":
        start, end = parse_date_range(message)
        if not start:
            return {"response": "Specify a timeframe like 'next week'."}

        cur.execute("""
            SELECT name FROM employees
            WHERE employee_id NOT IN (
                SELECT employee_id FROM assignments
                WHERE start_date <= %s AND end_date >= %s
            );
        """, (end, start))

        names = sorted(set([r[0] for r in cur.fetchall()]))

        if not names:
            return {"response": "No one is available then."}

        return {"response": ", ".join(names) + " are available."}

    # ------------------------------------
    # SKILL LOOKUP
    # ------------------------------------
    if intent == "skills":
        skills = parse_skills(message)
        if not skills:
            return {"response": "Specify skills like 'python' or 'django'."}

        where = " AND ".join([f"skills::text ILIKE '%{s}%'" for s in skills])
        cur.execute(f"SELECT name FROM employees WHERE {where};")

        names = sorted(set([r[0] for r in cur.fetchall()]))

        if not names:
            return {"response": "No employees found with those skills."}

        return {"response": "Employees with those skills: " + ", ".join(names)}

    # ------------------------------------
    # ASSIGNMENT LOOKUP
    # ------------------------------------
    if intent == "assignment":
        emp_id, full_name = parse_employee(message)
        if not emp_id:
            return {"response": "I couldn’t find that employee."}

        start, end = parse_date_range(message)
        if not start:
            return {"response": "Specify a timeframe like 'this week'."}

        cur.execute("""
            SELECT title
            FROM assignments
            WHERE employee_id = %s
              AND start_date <= %s
              AND end_date >= %s;
        """, (emp_id, end, start))

        tasks = [r[0] for r in cur.fetchall()]

        if not tasks:
            return {"response": f"{full_name} has no assignments in that period."}

        return {"response": f"{full_name} is working on: " + ", ".join(tasks)}

    # ------------------------------------
    # ROLE LOOKUP
    # ------------------------------------
    if intent == "role":
        cur.execute("SELECT name FROM employees WHERE LOWER(role) LIKE '%backend%';")
        names = sorted(set([r[0] for r in cur.fetchall()]))

        if not names:
            return {"response": "No backend developers found."}

        return {"response": "Backend developers: " + ", ".join(names)}

    # ------------------------------------
    # FALLBACK
    # ------------------------------------
    return {"response": "Sorry, I didn’t understand. Try asking about availability, roles, skills, or tasks."}
