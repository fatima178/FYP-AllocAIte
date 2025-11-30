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
        create table if not exists users (
            user_id serial primary key,
            name varchar(100),
            email varchar(100) unique,
            password_hash varchar(255),
            created_at timestamp default current_timestamp
        );
    """)

    # uploads table tracks each excel upload tied to a user
    # is_active marks which dataset is currently in use
    cur.execute("""
        create table if not exists uploads (
            upload_id serial primary key,
            user_id int references users(user_id),
            file_name varchar(255),
            upload_date timestamp default current_timestamp,
            is_active boolean default true
        );
    """)

    # employees table stores all staff from the uploaded dataset
    # skills stored as json list
    cur.execute("""
        create table if not exists employees (
            employee_id serial primary key,
            upload_id int references uploads(upload_id) on delete cascade,
            name varchar(100),
            role varchar(100),
            department varchar(100),
            experience_years float,
            skills json
        );
    """)

    # assignments table stores project assignments for employees
    # total_hours and remaining_hours allow availability calculations
    cur.execute("""
        create table if not exists assignments (
            assignment_id serial primary key,
            employee_id int references employees(employee_id) on delete cascade,
            upload_id int references uploads(upload_id) on delete cascade,
            title varchar(150),
            start_date date,
            end_date date,
            total_hours float,
            remaining_hours float,
            priority varchar(50)
        );
    """)

    # recommendations table stores optional nlp-based suggestions for future expansion
    cur.execute("""
        create table if not exists recommendations (
            rec_id serial primary key,
            assignment_id int references assignments(assignment_id) on delete cascade,
            employee_id int references employees(employee_id) on delete cascade,
            match_score float,
            reason text,
            generated_at timestamp default current_timestamp
        );
    """)

    # chatlogs store user queries and responses for auditing/debugging
    cur.execute("""
        create table if not exists chatlogs (
            chat_id serial primary key,
            user_id int references users(user_id),
            query_text text,
            response_text text,
            timestamp timestamp default current_timestamp
        );
    """)

    # user settings store theme and font size preferences
    cur.execute("""
        create table if not exists usersettings (
            user_id int primary key references users(user_id) on delete cascade,
            theme varchar(20) default 'light',
            font_size varchar(20) default 'medium'
        );
    """)

    # indexes to speed up availability calculations and dashboard queries
    cur.execute("create index if not exists idx_assign_employee on assignments(employee_id);")
    cur.execute("create index if not exists idx_assign_dates on assignments(start_date, end_date);")
    cur.execute("create index if not exists idx_emp_upload on employees(upload_id);")
    cur.execute("create index if not exists idx_upload_active on uploads(user_id, is_active);")

    conn.commit()
    cur.close()
    conn.close()
