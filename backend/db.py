# db.py
import psycopg2


def get_connection():
    conn = psycopg2.connect(
        dbname="allocaite",
        user="fatima",
        password=" ",
        host="localhost",
        port="5433"
    )
    return conn


def init_db():
    # initialises all required tables and indexes if they do not exist
    conn = get_connection()
    cur = conn.cursor()

    # users table stores basic account data
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Users" (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password_hash VARCHAR(255),
            account_type VARCHAR(20) DEFAULT 'manager',
            employee_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # uploads table tracks each excel upload tied to a user
    # is_active marks which dataset is currently in use
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Uploads" (
            upload_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES "Users"(user_id),
            file_name VARCHAR(255),
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
    """)

    # employees table stores all staff from the uploaded dataset
    # skills stored as json list
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Employees" (
            employee_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE,
            upload_id INT REFERENCES "Uploads"(upload_id) ON DELETE CASCADE,
            name VARCHAR(100),
            role VARCHAR(100),
            department VARCHAR(100)
        );
    """)

    # employee skills table stores per-skill experience for each employee
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "EmployeeSkills" (
            id SERIAL PRIMARY KEY,
            employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
            skill_name VARCHAR(100),
            years_experience FLOAT
        );
    """)

    # employee self-skills entered via their own portal
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "EmployeeSelfSkills" (
            id SERIAL PRIMARY KEY,
            employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
            skill_name VARCHAR(100),
            years_experience FLOAT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # employee learning goals (skills they want to develop)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "EmployeeLearningGoals" (
            id SERIAL PRIMARY KEY,
            employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
            skill_name VARCHAR(100),
            priority INT DEFAULT 3,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # employee preferences for future matching
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "EmployeePreferences" (
            employee_id INT PRIMARY KEY REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
            preferred_roles TEXT,
            preferred_departments TEXT,
            preferred_projects TEXT,
            growth_text TEXT,
            work_style TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # employee personal calendar entries (visible only to employee)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "EmployeeCalendarEntries" (
            entry_id SERIAL PRIMARY KEY,
            employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
            label TEXT,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # assignments table stores project assignments for employees
    # total_hours and remaining_hours allow availability calculations
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Assignments" (
            assignment_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE,
            employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
            upload_id INT REFERENCES "Uploads"(upload_id) ON DELETE CASCADE,
            title VARCHAR(150),
            start_date DATE,
            end_date DATE,
            total_hours FLOAT,
            remaining_hours FLOAT,
            priority VARCHAR(50)
        );
    """)

    # assignment history table stores past records for fairness tracking
    cur.execute("""
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
            priority VARCHAR(50),
            archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # recommendations table stores optional suggestions for future expansion
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Recommendations" (
            rec_id SERIAL PRIMARY KEY,
            assignment_id INT REFERENCES "Assignments"(assignment_id) ON DELETE CASCADE,
            employee_id INT REFERENCES "Employees"(employee_id) ON DELETE CASCADE,
            match_score FLOAT,
            reason TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # chatlogs store user queries and responses for auditing/debugging
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "ChatLogs" (
            chat_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES "Users"(user_id),
            query_text TEXT,
            response_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # user settings store theme and font size preferences
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "UserSettings" (
            user_id INT PRIMARY KEY REFERENCES "Users"(user_id) ON DELETE CASCADE,
            theme VARCHAR(20) DEFAULT 'light',
            font_size VARCHAR(20) DEFAULT 'medium',
            use_custom_weights BOOLEAN DEFAULT FALSE,
            weight_semantic FLOAT,
            weight_skill FLOAT,
            weight_experience FLOAT,
            weight_role FLOAT,
            weight_availability FLOAT,
            weight_fairness FLOAT,
            weight_preferences FLOAT
        );
    """)

    # employee invite tokens for account creation
    cur.execute("""
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
    """)

    cur.execute('ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS account_type VARCHAR(20) DEFAULT \'manager\';')
    cur.execute('ALTER TABLE "Users" ADD COLUMN IF NOT EXISTS employee_id INT;')
    cur.execute('ALTER TABLE "Employees" ADD COLUMN IF NOT EXISTS user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE;')
    cur.execute('ALTER TABLE "Uploads" ADD COLUMN IF NOT EXISTS upload_type VARCHAR(50) DEFAULT \'assignments\';')
    cur.execute('ALTER TABLE "Assignments" ADD COLUMN IF NOT EXISTS user_id INT REFERENCES "Users"(user_id) ON DELETE CASCADE;')
    cur.execute('ALTER TABLE "Employees" DROP COLUMN IF EXISTS experience_years;')
    cur.execute('ALTER TABLE "Employees" DROP COLUMN IF EXISTS skills;')
    cur.execute('ALTER TABLE "EmployeeLearningGoals" ADD COLUMN IF NOT EXISTS notes TEXT;')
    cur.execute('ALTER TABLE "EmployeePreferences" ADD COLUMN IF NOT EXISTS growth_text TEXT;')
    cur.execute('ALTER TABLE "EmployeeCalendarEntries" ADD COLUMN IF NOT EXISTS label TEXT;')
    cur.execute('ALTER TABLE "EmployeeCalendarEntries" ADD COLUMN IF NOT EXISTS start_date DATE;')
    cur.execute('ALTER TABLE "EmployeeCalendarEntries" ADD COLUMN IF NOT EXISTS end_date DATE;')
    cur.execute('ALTER TABLE "EmployeeCalendarEntries" DROP COLUMN IF EXISTS event_date;')
    cur.execute('ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS use_custom_weights BOOLEAN DEFAULT FALSE;')
    cur.execute('ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_semantic FLOAT;')
    cur.execute('ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_skill FLOAT;')
    cur.execute('ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_experience FLOAT;')
    cur.execute('ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_role FLOAT;')
    cur.execute('ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_availability FLOAT;')
    cur.execute('ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_fairness FLOAT;')
    cur.execute('ALTER TABLE "UserSettings" ADD COLUMN IF NOT EXISTS weight_preferences FLOAT;')
    cur.execute('UPDATE "Users" SET account_type = COALESCE(account_type, \'manager\');')
    # indexes to speed up availability calculations and dashboard queries
    cur.execute('CREATE INDEX IF NOT EXISTS idx_assign_employee ON "Assignments"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_assign_dates ON "Assignments"(start_date, end_date);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_assign_user ON "Assignments"(user_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_emp_upload ON "Employees"(upload_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_upload_active ON "Uploads"(user_id, is_active);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_emp_user ON "Employees"(user_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_skill_employee ON "EmployeeSkills"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_skill_name ON "EmployeeSkills"(skill_name);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_self_skill_employee ON "EmployeeSelfSkills"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_self_skill_name ON "EmployeeSelfSkills"(skill_name);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_goal_employee ON "EmployeeLearningGoals"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_goal_skill ON "EmployeeLearningGoals"(skill_name);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_pref_employee ON "EmployeePreferences"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_assign_hist_employee ON "AssignmentHistory"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_assign_hist_user ON "AssignmentHistory"(user_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_assign_hist_source ON "AssignmentHistory"(source_assignment_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_users_employee_id ON "Users"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_invite_token ON "EmployeeInvites"(token_hash);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_invite_employee ON "EmployeeInvites"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_emp_calendar_employee ON "EmployeeCalendarEntries"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_emp_calendar_start ON "EmployeeCalendarEntries"(start_date);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_emp_calendar_end ON "EmployeeCalendarEntries"(end_date);')

    conn.commit()
    cur.close()
    conn.close()
