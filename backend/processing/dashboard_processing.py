from db import get_connection
from datetime import date
import json
from typing import List, Optional


def get_dashboard_summary(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # get the latest active upload
        cur.execute("""
            SELECT upload_id
            FROM uploads
            WHERE is_active = TRUE
              AND user_id = %s
            ORDER BY upload_date DESC
            LIMIT 1;
        """, (user_id,))
        result = cur.fetchone()
        if not result:
            return {
                "total_employees": 0,
                "active_projects": 0,
                "available_this_week": 0
            }

        upload_id = result[0]
        today = date.today()

        # count how many unique employees are in the current upload
        cur.execute("""
            SELECT COUNT(DISTINCT name)
            FROM employees
            WHERE upload_id = %s;
        """, (upload_id,))
        total_employees = cur.fetchone()[0] or 0

        # count how many unique projects are still active (based on start and end date)
        cur.execute("""
            SELECT COUNT(*)
            FROM employees
            CROSS JOIN LATERAL jsonb_array_elements(
                COALESCE(active_assignments, '[]'::jsonb)
            ) AS elem
            WHERE upload_id = %s
              AND elem->>'start_date' IS NOT NULL
              AND elem->>'end_date' IS NOT NULL
              AND elem->>'start_date' NOT IN ('', 'NaT')
              AND elem->>'end_date' NOT IN ('', 'NaT')
              AND (elem->>'start_date')::date <= CURRENT_DATE
              AND (elem->>'end_date')::date >= CURRENT_DATE;
        """, (upload_id,))
        active_projects = cur.fetchone()[0] or 0

        # count how many employees are marked as available
        cur.execute("""
            SELECT COUNT(DISTINCT name)
            FROM employees
            WHERE upload_id = %s
              AND LOWER(availability_status) = 'available';
        """, (upload_id,))
        available_this_week = cur.fetchone()[0] or 0

        # return everything as one summary dictionary for the dashboard
        return {
            "total_employees": total_employees,
            "active_projects": active_projects,
            "available_this_week": available_this_week
        }

    finally:
        # close the database connection so nothing stays open
        cur.close()
        conn.close()


def _get_latest_upload_id(cur, user_id: int) -> Optional[int]:
    cur.execute(
        """
        SELECT upload_id
        FROM uploads
        WHERE is_active = TRUE
          AND user_id = %s
        ORDER BY upload_date DESC
        LIMIT 1;
        """,
        (user_id,),
    )
    result = cur.fetchone()
    return result[0] if result else None


def get_available_skills(user_id: int):
    """Return distinct skills for a user's latest upload so the UI can build filters."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        upload_id = _get_latest_upload_id(cur, user_id)
        if not upload_id:
            return {"skills": []}

        cur.execute(
            """
            SELECT skills
            FROM employees
            WHERE upload_id = %s;
            """,
            (upload_id,),
        )

        skill_set = set()
        for row in cur.fetchall():
            raw = row[0]
            if isinstance(raw, list):
                values = raw
            else:
                try:
                    values = json.loads(raw) if raw else []
                except (TypeError, json.JSONDecodeError):
                    values = []
            for skill in values:
                cleaned = str(skill).strip()
                if cleaned:
                    skill_set.add(cleaned)

        return {"skills": sorted(skill_set, key=lambda s: s.lower())}
    finally:
        cur.close()
        conn.close()


def get_employees_data(
    user_id: int,
    search: Optional[str] = None,
    skills: Optional[List[str]] = None,
    availability: Optional[str] = None,
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        upload_id = _get_latest_upload_id(cur, user_id)
        if not upload_id:
            return {"employees": []}

        # fetch all employees for that upload
        cur.execute("""
            SELECT 
                employee_id,
                name,
                role,
                department,
                experience_years,
                skills,
                availability_status,
                availability_percent,
                active_assignments
            FROM employees
            WHERE upload_id = %s
            ORDER BY name ASC;
        """, (upload_id,))

        rows = cur.fetchall()

        def parse_json_field(value, default):
            if isinstance(value, (list, dict)):
                return value
            if isinstance(value, str) and value.strip():
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return default
            return default

        search_term = search.strip().lower() if search else None
        skill_filters = [s.strip().lower() for s in (skills or []) if s and s.strip()]
        availability_filter = availability.strip().lower() if availability else None

        today = date.today()
        employees = []
        for r in rows:
            name = r[1] or ""
            # create initials (first and last letter of full name)
            parts = name.split()
            initials = ""
            if len(parts) >= 2:
                initials = parts[0][0] + parts[-1][0]
            elif len(parts) == 1:
                initials = parts[0][0]
            initials = initials.upper()

            parsed_skills = [s.strip() for s in parse_json_field(r[5], []) if s.strip()]
            skills_lower = [s.lower() for s in parsed_skills]
            availability_status = (r[6] or "").lower()

            # apply text search filter
            if search_term:
                role = (r[2] or "").lower()
                if search_term not in name.lower() and search_term not in role:
                    continue

            # apply skill filter (employee must have all selected skills)
            if skill_filters and not all(sf in skills_lower for sf in skill_filters):
                continue

            # apply availability filter
            if availability_filter and availability_status != availability_filter:
                continue

            assignments = []
            for assignment in parse_json_field(r[8], []):
                title = assignment.get("title")
                start_raw = assignment.get("start_date")
                end_raw = assignment.get("end_date")

                if not title or title in ["—", "-", "None", "NaN", ""]:
                    continue
                if not start_raw or not end_raw:
                    continue

                try:
                    start_date = date.fromisoformat(str(start_raw))
                    end_date = date.fromisoformat(str(end_raw))
                except ValueError:
                    continue

                if start_date <= today <= end_date:
                    assignments.append({
                        "title": title,
                        "priority": assignment.get("priority"),
                        "start_date": str(start_date),
                        "end_date": str(end_date)
                    })

            employees.append({
                "employee_id": r[0],
                "name": name,
                "initials": initials,
                "role": r[2],
                "department": r[3],
                "experience_years": r[4],
                "skills": parsed_skills,
                "availability_status": r[6],
                "availability_percent": float(r[7]) if r[7] is not None else None,
                "active_assignments": assignments
            })

        return {"employees": employees}

    finally:
        cur.close()
        conn.close()
