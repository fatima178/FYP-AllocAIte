# db.py
import psycopg2


def get_connection():
    # returns a fresh database connection; used throughout the app
    # connection details should normally come from environment variables
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
            upload_id INT REFERENCES "Uploads"(upload_id) ON DELETE CASCADE,
            name VARCHAR(100),
            role VARCHAR(100),
            department VARCHAR(100),
            experience_years FLOAT,
            skills JSON
        );
    """)

    # assignments table stores project assignments for employees
    # total_hours and remaining_hours allow availability calculations
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Assignments" (
            assignment_id SERIAL PRIMARY KEY,
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
            font_size VARCHAR(20) DEFAULT 'medium'
        );
    """)

    # indexes to speed up availability calculations and dashboard queries
    cur.execute('CREATE INDEX IF NOT EXISTS idx_assign_employee ON "Assignments"(employee_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_assign_dates ON "Assignments"(start_date, end_date);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_emp_upload ON "Employees"(upload_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_upload_active ON "Uploads"(user_id, is_active);')

    conn.commit()
    cur.close()
    conn.close()
