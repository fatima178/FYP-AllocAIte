import os

import psycopg2


def get_connection():
    # deployed databases usually provide a full DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)

    # local development can use the separate Postgres variables instead
    return psycopg2.connect(
        dbname=os.getenv("ALLOCATE_DB_NAME") or os.getenv("PGDATABASE", "allocaite"),
        user=os.getenv("ALLOCATE_DB_USER") or os.getenv("PGUSER", "fatima"),
        password=os.getenv("ALLOCATE_DB_PASSWORD") or os.getenv("PGPASSWORD", ""),
        host=os.getenv("ALLOCATE_DB_HOST") or os.getenv("PGHOST", "localhost"),
        port=os.getenv("ALLOCATE_DB_PORT") or os.getenv("PGPORT", "5433"),
)


# tables needed by the app when it starts with a fresh database
TABLE_DEFINITIONS = (
    """
    CREATE TABLE IF NOT EXISTS "Users" (
        user_id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        password_hash VARCHAR(255),
        account_type VARCHAR(20) DEFAULT 'manager',
        employee_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "Uploads" (
        upload_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES "Users"(user_id),
        file_name VARCHAR(255),
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "Employees" (
        employee_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE,
        upload_id INT REFERENCES "Uploads"(upload_id) ON DELETE CASCADE,
        name VARCHAR(100),
        role VARCHAR(100),
        department VARCHAR(100)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "EmployeeSkills" (
        id SERIAL PRIMARY KEY,
        employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
        skill_name VARCHAR(100),
        years_experience FLOAT,
        skill_type VARCHAR(20) DEFAULT 'technical'
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "EmployeeSelfSkills" (
        id SERIAL PRIMARY KEY,
        employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
        skill_name VARCHAR(100),
        years_experience FLOAT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "EmployeeLearningGoals" (
        id SERIAL PRIMARY KEY,
        employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
        skill_name VARCHAR(100),
        priority INT DEFAULT 3,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "EmployeePreferences" (
        employee_id INT PRIMARY KEY REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
        preferred_roles TEXT,
        preferred_departments TEXT,
        preferred_projects TEXT,
        growth_text TEXT,
        work_style TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "EmployeeCalendarEntries" (
        entry_id SERIAL PRIMARY KEY,
        employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
        label TEXT,
        start_date DATE,
        end_date DATE,
        total_hours FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "Assignments" (
        assignment_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE,
        employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
        upload_id INT REFERENCES "Uploads"(upload_id) ON DELETE CASCADE,
        title VARCHAR(150),
        start_date DATE,
        end_date DATE,
        total_hours FLOAT,
        remaining_hours FLOAT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "AssignmentHistory" (
        history_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE,
        employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
        upload_id INT REFERENCES "Uploads"(upload_id) ON DELETE SET NULL,
        source_assignment_id INT,
        title VARCHAR(150),
        start_date DATE,
        end_date DATE,
        total_hours FLOAT,
        remaining_hours FLOAT,
        archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "RecommendationTasks" (
        task_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE,
        task_description TEXT,
        start_date DATE,
        end_date DATE,
        assignment_id INT REFERENCES "Assignments"(assignment_id) ON DELETE SET NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "RecommendationLog" (
        log_id SERIAL PRIMARY KEY,
        task_id INT REFERENCES "RecommendationTasks"(task_id) ON DELETE CASCADE,
        employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
        recommendation_rank INT,
        recommendation_score FLOAT,
        manager_selected BOOLEAN DEFAULT FALSE,
        performance_rating VARCHAR(20),
        feedback_notes TEXT,
        outcome_tags TEXT,
        feedback_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CHECK (performance_rating IS NULL OR performance_rating IN ('Excellent', 'Good', 'Average', 'Poor'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "ChatLogs" (
        chat_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES "Users"(user_id),
        query_text TEXT,
        response_text TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "UserSettings" (
        user_id INT PRIMARY KEY REFERENCES "Users"(user_id) ON DELETE CASCADE,
        theme VARCHAR(20) DEFAULT 'light',
        font_size VARCHAR(20) DEFAULT 'medium',
        use_custom_weights BOOLEAN DEFAULT FALSE,
        weight_semantic FLOAT,
        weight_skill FLOAT,
        weight_possible_skill FLOAT,
        weight_soft_skill FLOAT,
        weight_possible_soft_skill FLOAT,
        weight_experience FLOAT,
        weight_role FLOAT,
        weight_availability FLOAT,
        weight_fairness FLOAT,
        weight_preferences FLOAT,
        weight_feedback FLOAT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS "EmployeeInvites" (
        invite_id SERIAL PRIMARY KEY,
        manager_user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE,
        employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
        email VARCHAR(100),
        token_hash VARCHAR(128),
        expires_at TIMESTAMP,
        used_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
)


# lightweight migrations for columns added while developing the project
# these are safe to run repeatedly because they use IF NOT EXISTS where possible
SCHEMA_UPDATES = (
    'ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS account_type VARCHAR(20) DEFAULT \'manager\';',
    'ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS employee_id INT;',
    'ALTER TABLE "Employees" ADD COLUMN IF NOT EXISTS user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE;',
    'ALTER TABLE "Uploads" ADD COLUMN IF NOT EXISTS upload_type VARCHAR(50) DEFAULT \'assignments\';',
    'ALTER TABLE "Assignments" ADD COLUMN IF NOT EXISTS user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE;',
    'ALTER TABLE "Employees" DROP COLUMN IF EXISTS experience_years;',
    'ALTER TABLE "Employees" DROP COLUMN IF EXISTS skills;',
    'ALTER TABLE "EmployeeSkills" ADD COLUMN IF NOT EXISTS skill_type VARCHAR(20) DEFAULT \'technical\';',
    'UPDATE "EmployeeSkills" SET skill_type = COALESCE(skill_type, \'technical\');',
    'ALTER TABLE "EmployeeLearningGoals" ADD COLUMN IF NOT EXISTS notes TEXT;',
    'ALTER TABLE "EmployeePreferences" ADD COLUMN IF NOT EXISTS growth_text TEXT;',
    'ALTER TABLE "EmployeeSelfSkills" ADD COLUMN IF NOT EXISTS skill_type VARCHAR(20) DEFAULT \'technical\';',
    'ALTER TABLE "EmployeeSelfSkills" ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT \'pending\';',
    'ALTER TABLE "EmployeeSelfSkills" ADD COLUMN IF NOT EXISTS approved_by_user_id INT REFERENCES "Users"(user_id) ON DELETE SET NULL;',
    'ALTER TABLE "EmployeeSelfSkills" ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;',
    'ALTER TABLE "EmployeeSelfSkills" ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP;',
    'UPDATE "EmployeeSelfSkills" SET skill_type = COALESCE(skill_type, \'technical\');',
    'UPDATE "EmployeeSelfSkills" SET status = COALESCE(status, \'pending\');',
    'ALTER TABLE "EmployeeCalendarEntries" ADD COLUMN IF NOT EXISTS total_hours FLOAT;',
    'ALTER TABLE "EmployeeCalendarEntries" ADD COLUMN IF NOT EXISTS label TEXT;',
    'ALTER TABLE "EmployeeCalendarEntries" ADD COLUMN IF NOT EXISTS start_date DATE;',
    'ALTER TABLE "EmployeeCalendarEntries" ADD COLUMN IF NOT EXISTS end_date DATE;',
    'ALTER TABLE "EmployeeCalendarEntries" DROP COLUMN IF EXISTS event_date;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS use_custom_weights BOOLEAN DEFAULT FALSE;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_semantic FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_skill FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_possible_skill FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_soft_skill FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_possible_soft_skill FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_experience FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_role FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_availability FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_fairness FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_preferences FLOAT;',
    'ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_feedback FLOAT;',
    'UPDATE "Users" SET account_type = COALESCE(account_type, \'manager\');',
    'ALTER TABLE "RecommendationTasks" ADD COLUMN IF NOT EXISTS assignment_id INT REFERENCES "Assignments"(assignment_id) ON DELETE SET NULL;',
    'ALTER TABLE "RecommendationLog" ADD COLUMN IF NOT EXISTS outcome_tags TEXT;',
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'employee_self_skills_status_check'
        ) THEN
            ALTER TABLE "EmployeeSelfSkills"
            ADD CONSTRAINT employee_self_skills_status_check
            CHECK (status IN ('pending', 'approved', 'rejected'));
        END IF;
    END
    $$;
    """,
)


# indexes for the queries used most often by dashboard, tasks, invites and history
INDEX_DEFINITIONS = (
    'CREATE INDEX IF NOT EXISTS idx_assign_employee ON "Assignments"(employee_id);',
    'CREATE INDEX IF NOT EXISTS idx_assign_dates ON "Assignments"(start_date, end_date);',
    'CREATE INDEX IF NOT EXISTS idx_assign_user ON "Assignments"(user_id);',
    'CREATE INDEX IF NOT EXISTS idx_emp_upload ON "Employees"(upload_id);',
    'CREATE INDEX IF NOT EXISTS idx_upload_active ON "Uploads"(user_id, is_active);',
    'CREATE INDEX IF NOT EXISTS idx_emp_user ON "Employees"(user_id);',
    'CREATE INDEX IF NOT EXISTS idx_skill_employee ON "EmployeeSkills"(employee_id);',
    'CREATE INDEX IF NOT EXISTS idx_skill_name ON "EmployeeSkills"(skill_name);',
    'CREATE INDEX IF NOT EXISTS idx_skill_type ON "EmployeeSkills"(skill_type);',
    'CREATE INDEX IF NOT EXISTS idx_self_skill_employee ON "EmployeeSelfSkills"(employee_id);',
    'CREATE INDEX IF NOT EXISTS idx_self_skill_name ON "EmployeeSelfSkills"(skill_name);',
    'CREATE INDEX IF NOT EXISTS idx_self_skill_status ON "EmployeeSelfSkills"(status);',
    'CREATE INDEX IF NOT EXISTS idx_goal_employee ON "EmployeeLearningGoals"(employee_id);',
    'CREATE INDEX IF NOT EXISTS idx_goal_skill ON "EmployeeLearningGoals"(skill_name);',
    'CREATE INDEX IF NOT EXISTS idx_pref_employee ON "EmployeePreferences"(employee_id);',
    'CREATE INDEX IF NOT EXISTS idx_assign_hist_employee ON "AssignmentHistory"(employee_id);',
    'CREATE INDEX IF NOT EXISTS idx_assign_hist_user ON "AssignmentHistory"(user_id);',
    'CREATE INDEX IF NOT EXISTS idx_assign_hist_source ON "AssignmentHistory"(source_assignment_id);',
    'CREATE INDEX IF NOT EXISTS idx_users_employee_id ON "Users"(employee_id);',
    'CREATE INDEX IF NOT EXISTS idx_invite_token ON "EmployeeInvites"(token_hash);',
    'CREATE INDEX IF NOT EXISTS idx_invite_employee ON "EmployeeInvites"(employee_id);',
    'CREATE INDEX IF NOT EXISTS idx_emp_calendar_employee ON "EmployeeCalendarEntries"(employee_id);',
    'CREATE INDEX IF NOT EXISTS idx_emp_calendar_start ON "EmployeeCalendarEntries"(start_date);',
    'CREATE INDEX IF NOT EXISTS idx_emp_calendar_end ON "EmployeeCalendarEntries"(end_date);',
    'CREATE INDEX IF NOT EXISTS idx_rec_task_user ON "RecommendationTasks"(user_id);',
    'CREATE INDEX IF NOT EXISTS idx_rec_task_assignment ON "RecommendationTasks"(assignment_id);',
    'CREATE INDEX IF NOT EXISTS idx_rec_log_task ON "RecommendationLog"(task_id);',
    'CREATE INDEX IF NOT EXISTS idx_rec_log_employee ON "RecommendationLog"(employee_id);',
)


def _execute_all(cur, statements):
    # run a group of SQL statements in order
    for statement in statements:
        cur.execute(statement)


def init_db():
    # called once when the FastAPI app starts
    # creates missing tables, applies simple schema updates, then adds indexes
    conn = get_connection()
    cur = conn.cursor()

    try:
        _execute_all(cur, TABLE_DEFINITIONS)
        _execute_all(cur, SCHEMA_UPDATES)
        _execute_all(cur, INDEX_DEFINITIONS)
        conn.commit()
    finally:
        cur.close()
        conn.close()
