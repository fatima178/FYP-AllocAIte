# routers/dashboard.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from processing.dashboard_processing import (
    get_dashboard_summary,
    get_employees_data,
)
from db import get_connection

router = APIRouter()


@router.get("/dashboard/summary")
def dashboard_summary(user_id: int):
    try:
        return get_dashboard_summary(user_id)
    except Exception as e:
        raise HTTPException(500, str(e))


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


@router.get("/dashboard/skills")
def dashboard_skills(user_id: int):
    """
    Returns list of all distinct skills in the current upload.
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT upload_id
            FROM Uploads
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY upload_date DESC
            LIMIT 1;
        """, (user_id,))
        row = cur.fetchone()
        if not row:
            return {"skills": []}

        upload_id = row[0]

        cur.execute("""
            SELECT skills
            FROM Employees
            WHERE upload_id = %s;
        """, (upload_id,))
        raw = cur.fetchall()

        all_skills = set()
        import json

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

        return {"skills": sorted(all_skills, key=lambda x: x.lower())}

    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        cur.close()
        conn.close()
