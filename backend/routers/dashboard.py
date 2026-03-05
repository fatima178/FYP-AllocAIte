# routers/dashboard.py

from datetime import date
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from processing.dashboard_processing import (
    get_dashboard_summary,
    get_employees_data,
)
from db import get_connection

router = APIRouter()


# ----------------------------------------------------------
# dashboard summary endpoint
# ----------------------------------------------------------
# returns top level numbers for the dashboard:
#   - total employees
#   - active projects
#   - available in next 7 days
# errors bubble up as 500 if unexpected.
@router.get("/dashboard/summary")
def dashboard_summary(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    try:
        start = None
        end = None
        if start_date or end_date:
            if not start_date or not end_date:
                raise HTTPException(400, "start_date and end_date must be provided together")
            try:
                start = date.fromisoformat(start_date)
                end = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(400, "start_date/end_date must be in YYYY-MM-DD format")

            if start > end:
                start, end = end, start

        return get_dashboard_summary(user_id, start, end)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ----------------------------------------------------------
# employee listing endpoint
# ----------------------------------------------------------
# supports filtering by:
#   - search text (name/role)
#   - skills (list)
#   - availability status
# returns structured employee data + availability + active assignments.
@router.get("/dashboard/employees")
def dashboard_employees(
    user_id: int,
    search: Optional[str] = None,
    skills: Optional[List[str]] = Query(None),
    availability: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    try:
        start = None
        end = None
        if start_date or end_date:
            if not start_date or not end_date:
                raise HTTPException(400, "start_date and end_date must be provided together")
            try:
                start = date.fromisoformat(start_date)
                end = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(400, "start_date/end_date must be in YYYY-MM-DD format")

            if start > end:
                start, end = end, start

        return get_employees_data(user_id, search, skills, availability, start, end)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ----------------------------------------------------------
# list all unique skills in user’s current upload
# ----------------------------------------------------------
# used for generating filter dropdowns on the dashboard.
@router.get("/dashboard/skills")
def dashboard_skills(user_id: int):
    """
    returns list of all distinct skills in the current upload.
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT DISTINCT skill_name
            FROM "EmployeeSkills"
            WHERE skill_type = 'technical'
              AND employee_id IN (
                  SELECT employee_id FROM "Employees" WHERE user_id = %s
              );
        """, (user_id,))
        raw = cur.fetchall()

        all_skills = set()
        for (skill_name,) in raw:
            s = str(skill_name).strip()
            if s:
                all_skills.add(s)

        # sorted for stable frontend display
        return {"skills": sorted(all_skills, key=lambda x: x.lower())}

    except Exception as e:
        raise HTTPException(500, str(e))

    finally:
        cur.close()
        conn.close()
