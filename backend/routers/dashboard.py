# routers/dashboard.py

from datetime import date
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from processing.dashboard.dashboard_processing import (
    get_dashboard_summary,
    get_employees_data,
)
from db import get_connection
from utils.request_utils import parse_date_range

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
        start, end = parse_date_range(
            start_date,
            end_date,
            normalize_order=True,
        )
        return get_dashboard_summary(user_id, start, end)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(400, str(exc).replace("valid ISO date", "must be in YYYY-MM-DD format"))
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
        start, end = parse_date_range(
            start_date,
            end_date,
            normalize_order=True,
        )
        return get_employees_data(user_id, search, skills, availability, start, end)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(400, str(exc).replace("valid ISO date", "must be in YYYY-MM-DD format"))
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
