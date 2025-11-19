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
    conn = get_connection()
    cur = conn.cursor()

    # ----------------------------------------------------------------------
    # 1. CLEAN OLD STRUCTURES
    # ----------------------------------------------------------------------
    # Nukes obsolete versions of the tables so your schema doesn't explode.
    cur.execute("DROP TABLE IF EXISTS Assignments CASCADE;")
    cur.execute("DROP TABLE IF EXISTS Employees CASCADE;")
    cur.execute("DROP TABLE IF EXISTS Uploads CASCADE;")
    # NOTE: Users is preserved because you shouldn't nuke your accounts.

    # ----------------------------------------------------------------------
    # 2. USERS TABLE
    # ----------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password_hash VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ----------------------------------------------------------------------
    # 3. UPLOADS TABLE
    # ----------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Uploads (
            upload_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES Users(user_id),
            file_name VARCHAR(255),
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
    """)

    # ----------------------------------------------------------------------
    # 4. EMPLOYEES TABLE (normalized, no assignment JSON)
    # ----------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Employees (
            employee_id SERIAL PRIMARY KEY,
            upload_id INT REFERENCES Uploads(upload_id) ON DELETE CASCADE,
            name VARCHAR(100),
            role VARCHAR(100),
            department VARCHAR(100),
            experience_years FLOAT,
            skills JSON
        );
    """)

    # ----------------------------------------------------------------------
    # 5. ASSIGNMENTS TABLE (normalized, one row per project/task)
    # ----------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Assignments (
            assignment_id SERIAL PRIMARY KEY,
            employee_id INT REFERENCES Employees(employee_id) ON DELETE CASCADE,
            upload_id INT REFERENCES Uploads(upload_id) ON DELETE CASCADE,

            title VARCHAR(150),
            start_date DATE,
            end_date DATE,

            total_hours FLOAT,
            remaining_hours FLOAT,
            priority VARCHAR(50)
        );
    """)

    # ----------------------------------------------------------------------
    # 6. RECOMMENDATIONS TABLE (future NLP)
    # ----------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Recommendations (
            rec_id SERIAL PRIMARY KEY,
            assignment_id INT REFERENCES Assignments(assignment_id) ON DELETE CASCADE,
            employee_id INT REFERENCES Employees(employee_id) ON DELETE CASCADE,
            match_score FLOAT,
            reason TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ----------------------------------------------------------------------
    # 7. CHATLOGS TABLE (for your rule-based chatbot)
    # ----------------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ChatLogs (
            chat_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES Users(user_id),
            query_text TEXT,
            response_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ----------------------------------------------------------------------
    # 8. INDEXES (makes availability + dashboard queries fast)
    # ----------------------------------------------------------------------
    cur.execute("CREATE INDEX IF NOT EXISTS idx_assign_employee ON Assignments(employee_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_assign_dates ON Assignments(start_date, end_date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_emp_upload ON Employees(upload_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_upload_active ON Uploads(user_id, is_active);")

    conn.commit()
    cur.close()
    conn.close()
