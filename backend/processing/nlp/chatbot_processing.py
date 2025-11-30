from datetime import datetime, timedelta
from dateutil import parser
import re

from db import get_connection


# parses natural language date expressions into an actual date range.
# this function supports keywords (today, tomorrow, next week, this week, next month),
# explicit iso dates, and fuzzy natural formats.
# returns (start_date, end_date). if parsing fails, returns (none, none).
def parse_date_range(text: str):
    t = text.lower().strip()
    now = datetime.today()

    # direct keyword: tomorrow
    if "tomorrow" in t:
        d = now + timedelta(days=1)
        return d.date(), d.date()

    # direct keyword: today
    if "today" in t:
        return now.date(), now.date()

    # pattern: "in x days"
    match = re.search(r"in (\d+) days", t)
    if match:
        offset = int(match.group(1))
        d = now + timedelta(days=offset)
        return d.date(), d.date()

    # keyword: next week (monday to sunday)
    if "next week" in t:
        # calculate next monday based on weekday
        start = now + timedelta(days=(7 - now.weekday()))
        end = start + timedelta(days=6)
        return start.date(), end.date()

    # keyword: this week (current monday to sunday)
    if "this week" in t:
        start = now - timedelta(days=now.weekday())
        end = start + timedelta(days=6)
        return start.date(), end.date()

    # keyword: next month (first day to last day of next month)
    if "next month" in t:
        # move to next month by jumping 32 days forward, then resetting day
        first = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
        # find end of month by jumping 32 more days and stepping back 1
        last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return first.date(), last.date()

    # detect explicit iso dates like "2025-03-20"
    iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", t)
    if len(iso_dates) >= 1:
        try:
            # if 1 date: treat as start=end
            # if 2+: treat first as start, last as end
            start = parser.parse(iso_dates[0]).date()
            end = parser.parse(iso_dates[-1]).date()
            return start, end
        except Exception:
            # ignore parsing error
            pass

    # fuzzy parse for things like "feb 5", "next friday", "4 march", etc.
    try:
        d = parser.parse(t, fuzzy=True).date()
        return d, d
    except Exception:
        return None, None


# extracts known technical skills from user input.
# uses simple keyword search over a predefined list of skills.
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
    # return only skills actually mentioned in the text
    return [s for s in known if s in t]


# attempts to identify an employee in the message.
# matches either the full name or the first name.
# returns (employee_id, employee_name) or (none, none) if not found.
def parse_employee(cur, upload_id, text: str):
    t = text.lower()

    # fetch all employees from this upload so we can match names locally
    cur.execute(
        "select employee_id, name from employees where upload_id = %s;",
        (upload_id,),
    )
    rows = cur.fetchall()

    # loop through employees and check if full name or first name appears in the message
    for emp_id, full_name in rows:
        full = full_name.lower()
        first = full.split(" ")[0]

        if full in t or first in t:
            return emp_id, full_name

    return None, None


# simple intent classifier based on keywords.
# determines what the user is asking about so the chatbot knows which handler to call.
def detect_intent(text: str):
    t = text.lower()

    # checking someone's schedule or free time
    if "available" in t or "free" in t or "busy" in t:
        return "availability"

    # checking what task someone is doing
    if "doing" in t or "working on" in t or "assigned" in t or "task" in t:
        return "assignment"

    # checking what skills someone has
    if "skill" in t or "knows" in t or "expert" in t or "has" in t:
        return "skills"

    # checking by job role
    if "backend" in t or "developer" in t or "designer" in t or "analyst" in t:
        return "role"

    # default when no intent matches
    return "fallback"


# handles "who is available on date x" style questions.
# uses overlapping date logic to filter employees.
def handle_availability(cur, upload_id: int, message: str):
    # first parse the date range from the message
    start, end = parse_date_range(message)
    if not start:
        return {
            "response": (
                "i couldn’t understand the timeframe. try 'next week', 'tomorrow', "
                "or a date like 2025-02-10."
            )
        }

    # select all employees who do not appear in an overlapping assignment window.
    # overlapping condition: assignment.start <= query.end and assignment.end >= query.start
    cur.execute(
        """
        select name from employees
        where upload_id = %s
          and employee_id not in (
              select employee_id from assignments
              where upload_id = %s
                and start_date <= %s
                and end_date >= %s
          );
        """,
        (upload_id, upload_id, end, start),
    )

    # get names, deduplicate and sort alphabetically for clean output
    names = sorted(set([r[0] for r in cur.fetchall()]))

    if not names:
        return {"response": f"no one is available between {start} and {end}."}

    return {
        "response": f"available between {start} and {end}: " + ", ".join(names)
    }


# handles "who knows python" or "show employees with sql and django" queries.
def handle_skills(cur, upload_id: int, message: str):
    skills = parse_skills(message)
    if not skills:
        return {"response": "specify a skill (e.g., python, sql, ui design)."}

    # build dynamic sql conditions based on number of skills detected
    # each condition checks whether the skill appears inside the skills json/text field
    conditions = []
    params = [upload_id]
    for skill in skills:
        conditions.append("skills::text ilike %s")
        params.append(f"%{skill}%")

    where_clause = " and ".join(conditions)

    query = f"""
        select name
        from employees
        where upload_id = %s
          and {where_clause};
    """
    cur.execute(query, params)

    names = sorted(set([r[0] for r in cur.fetchall()]))

    if not names:
        return {"response": "no employees found with those skills."}

    return {"response": f"employees with {', '.join(skills)}: " + ", ".join(names)}


# handles questions like "what is alice doing next week?"
# combines employee name detection + date parsing + assignment overlap filtering.
def handle_assignment(cur, upload_id: int, message: str):
    # figure out which employee the user is asking about
    emp_id, full_name = parse_employee(cur, upload_id, message)
    if not emp_id:
        return {
            "response": "i couldn’t find that employee. try full or first name."
        }

    # figure out the date range the user mentioned
    start, end = parse_date_range(message)
    if not start:
        return {
            "response": (
                "specify a timeframe (e.g., 'this week', 'tomorrow', or '2025-02-05')."
            )
        }

    # get all assignments overlapping this date range for this employee
    cur.execute(
        """
        select title
        from assignments
        where employee_id = %s
          and upload_id = %s
          and start_date <= %s
          and end_date >= %s;
        """,
        (emp_id, upload_id, end, start),
    )

    tasks = [r[0] for r in cur.fetchall()]

    # respond depending on whether tasks exist
    if not tasks:
        return {"response": f"{full_name} has no tasks between {start} and {end}."}

    return {"response": f"{full_name} is working on: " + ", ".join(tasks)}


# handles role-based queries such as "show me designers" or "list backend developers".
def handle_role(cur, upload_id: int):
    cur.execute(
        """
        select name from employees
        where upload_id = %s
          and (
              lower(role) like '%%backend%%'
              or lower(role) like '%%developer%%'
              or lower(role) like '%%designer%%'
              or lower(role) like '%%analyst%%'
          );
        """,
        (upload_id,),
    )
    names = sorted(set([r[0] for r in cur.fetchall()]))

    if not names:
        return {"response": "no developers found."}

    return {"response": "developers: " + ", ".join(names)}


# finds the current active upload for this user.
# if there is no active upload, fallback to the most recently uploaded file.
def resolve_upload_id(cur, user_id: int):
    # check for an explicitly active upload
    cur.execute(
        """
        select upload_id
        from uploads
        where user_id = %s and is_active = true
        order by upload_date desc
        limit 1;
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # fallback to last upload ever made by this user
    cur.execute(
        """
        select upload_id
        from uploads
        where user_id = %s
        order by upload_date desc
        limit 1;
        """,
        (user_id,),
    )
    row = cur.fetchone()
    return row[0] if row else None


# central handler for all chatbot queries.
# this function decides which sub-handler to call based on detected intent.
# it also manages database connection lifecycle.
def handle_chatbot_query(message: str, user_id: int):
    # basic validation: message and user must be present
    message = (message or "").strip()
    if not message:
        raise ValueError("missing message")
    if not user_id:
        raise ValueError("missing user_id")

    # classify the user's request
    intent = detect_intent(message)

    # open db connection
    conn = get_connection()
    cur = conn.cursor()

    try:
        # find which dataset (upload) to use
        upload_id = resolve_upload_id(cur, user_id)
        if not upload_id:
            return {
                "response": "no employee data found. please upload your team sheet first."
            }

        # call the correct handler depending on intent
        if intent == "availability":
            return handle_availability(cur, upload_id, message)
        if intent == "skills":
            return handle_skills(cur, upload_id, message)
        if intent == "assignment":
            return handle_assignment(cur, upload_id, message)
        if intent == "role":
            return handle_role(cur, upload_id)

        # default fallback response when nothing matches
        return {
            "response": "i didn’t understand that. try asking about availability, skills, roles, or assignments."
        }
    finally:
        # always close database cursor and connection to avoid leaks
        cur.close()
        conn.close()
