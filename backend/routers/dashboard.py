# routers/dashboard.py

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
def dashboard_summary(user_id: int):
    try:
        return get_dashboard_summary(user_id)
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
):
    try:
        return get_employees_data(user_id, search, skills, availability)
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
        # find active upload for this user
        cur.execute("""
            SELECT upload_id
            FROM "Uploads"
            WHERE user_id = %s AND is_active = true
            ORDER BY upload_date DESC
            LIMIT 1;
        """, (user_id,))
        row = cur.fetchone()

        if not row:
            # user has no uploads yet
            return {"skills": []}

        upload_id = row[0]

        # fetch skills column from all employees
        cur.execute("""
            SELECT skills
            FROM "Employees"
            WHERE upload_id = %s;
        """, (upload_id,))
        raw = cur.fetchall()

        all_skills = set()
        import json

        # normalise/parse skills into a flattened set
        for (skill_json,) in raw:
            if isinstance(skill_json, list):
                skills = skill_json
            else:
                try:
                    skills = json.loads(skill_json)
                except:
                    skills = []

            for s in skills:
                s = str(s).strip()
                if s:
                    all_skills.add(s)

        # sorted for stable frontend display
        return {"skills": sorted(all_skills, key=lambda x: x.lower())}

    except Exception as e:
        raise HTTPException(500, str(e))

    finally:
        cur.close()
        conn.close()
