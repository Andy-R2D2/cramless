"""
database.py — SHARED by everyone.

Creates the SQLite database (cramless.db) and all the tables, so the whole
team agrees on the same structure from day one.

Run once to create the database:
    python database.py

If you need a new column, tell the team first, add it here, then delete
cramless.db and run this file again (we don't have real data yet).
"""

import sqlite3

DB_FILE = "cramless.db"


def get_connection():
    """Open a connection to the database. Rows behave like dicts: row["name"]."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # make ON DELETE CASCADE work
    return conn


def create_tables():
    """Create every table if it doesn't exist yet."""
    conn = get_connection()
    conn.executescript(
        """
        -- Role 1: student accounts
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,          -- never store plain passwords!
            language      TEXT DEFAULT 'en'       -- 'en' or 'fr'
        );

        -- Role 2: courses and lectures
        CREATE TABLE IF NOT EXISTS courses (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            code    TEXT NOT NULL,                -- e.g. 'CSCI 3230U'
            name    TEXT NOT NULL                 -- e.g. 'Web Development'
        );

        CREATE TABLE IF NOT EXISTS lectures (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            number    INTEGER NOT NULL,           -- 1, 2, 3 ... (Lecture 1 to current)
            title     TEXT NOT NULL,
            pdf_path  TEXT NOT NULL,              -- file saved in the uploads/ folder
            reviewed  INTEGER DEFAULT 0,          -- 1 once the student opened it (readiness)
            original_filename TEXT,               -- name of the file the student uploaded (shown on the course page)
            uploaded_at       TEXT                -- 'YYYY-MM-DD'
        );

        CREATE TABLE IF NOT EXISTS summaries (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id   INTEGER UNIQUE NOT NULL REFERENCES lectures(id) ON DELETE CASCADE,
            key_concepts TEXT,
            explanation  TEXT,
            examples     TEXT
        );

        CREATE TABLE IF NOT EXISTS flashcards (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            lecture_id    INTEGER NOT NULL REFERENCES lectures(id) ON DELETE CASCADE,
            question      TEXT NOT NULL,          -- may contain LaTeX, e.g. $x^2$
            answer        TEXT NOT NULL,
            times_known   INTEGER DEFAULT 0,      -- "knew it" clicks
            times_missed  INTEGER DEFAULT 0,      -- "didn't know" clicks
            last_reviewed TEXT                    -- date as 'YYYY-MM-DD'
        );

        -- Role 3: planning and study time
        CREATE TABLE IF NOT EXISTS exams (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id    INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            kind         TEXT NOT NULL,           -- 'midterm' or 'final'
            exam_date    TEXT NOT NULL,           -- 'YYYY-MM-DD'
            is_tentative INTEGER DEFAULT 1        -- students may not know the exact date
        );

        CREATE TABLE IF NOT EXISTS class_times (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            course_id  INTEGER REFERENCES courses(id) ON DELETE CASCADE,
            weekday    INTEGER NOT NULL,          -- 0 = Monday ... 6 = Sunday
            start_time TEXT NOT NULL,             -- 'HH:MM'
            end_time   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_goals (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            weekday       INTEGER NOT NULL,       -- 0 = Monday ... 6 = Sunday
            hours         REAL NOT NULL,          -- e.g. 3 means 3 hours on that day
            reminder_time TEXT,                   -- 'HH:MM', used by Role 4
            UNIQUE (user_id, weekday)             -- one goal per day of the week
        );

        CREATE TABLE IF NOT EXISTS study_sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            course_id  INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            study_date TEXT NOT NULL,             -- 'YYYY-MM-DD'
            minutes    INTEGER NOT NULL,
            source     TEXT NOT NULL              -- 'timer' or 'offline'
        );
        """
    )
    _add_missing_columns(conn)
    conn.commit()
    conn.close()


def _add_missing_columns(conn):
    """
    Upgrade databases created before a column was added, so teammates
    don't have to delete their cramless.db. (CREATE TABLE IF NOT EXISTS
    doesn't add new columns to a table that already exists.)
    """
    new_columns = {
        # table: [(column, type), ...]
        "lectures": [("original_filename", "TEXT"), ("uploaded_at", "TEXT")],
    }
    for table, columns in new_columns.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for column, col_type in columns:
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


if __name__ == "__main__":
    create_tables()
    print(f"Database ready: {DB_FILE}")
