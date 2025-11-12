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

    # USERS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password_hash VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # UPLOADS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Uploads (
            upload_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES Users(user_id),
            file_name VARCHAR(255),
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN
        );
    """)

    # EMPLOYEES TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Employees (
            employee_id SERIAL PRIMARY KEY,
            upload_id INT REFERENCES Uploads(upload_id),
            name VARCHAR(100),
            role VARCHAR(100),
            experience_years FLOAT,
            skills JSON,
            availability_status VARCHAR(20),
            availability_percent FLOAT,
            department VARCHAR(100),
            active_assignments JSON
        );
    """)
    cur.execute("""
        ALTER TABLE Employees
        ADD COLUMN IF NOT EXISTS availability_percent FLOAT;
    """)

    # ASSIGNMENTS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Assignments (
            assignment_id SERIAL PRIMARY KEY,
            upload_id INT REFERENCES Uploads(upload_id),
            title VARCHAR(150),
            description TEXT,
            required_skills JSON,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # RECOMMENDATIONS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Recommendations (
            rec_id SERIAL PRIMARY KEY,
            assignment_id INT REFERENCES Assignments(assignment_id),
            employee_id INT REFERENCES Employees(employee_id),
            match_score FLOAT,
            reason TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # CHATLOGS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ChatLogs (
            chat_id SERIAL PRIMARY KEY,
            user_id INT REFERENCES Users(user_id),
            query_text TEXT,
            response_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
