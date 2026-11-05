"""
auth.py — ROLE 1. Register and log in students (functionality #2).

Passwords are hashed with werkzeug (installed with Flask), so we never
store the real password in the database.
"""

from werkzeug.security import check_password_hash, generate_password_hash

from database import get_connection


def register_user(email, password):
    """
    Create a new student account.
    Returns the new user's id, or None if the email is already used.
    """
    # TODO (Role 1): reject empty emails and passwords shorter than 8 characters
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return None

    cursor = conn.execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (email, generate_password_hash(password)),  # hash, never the plain password
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def check_login(email, password):
    """
    Check an email + password.
    Returns the user's id if correct, otherwise None.
    """
    conn = get_connection()
    user = conn.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if user and check_password_hash(user["password_hash"], password):
        return user["id"]
    return None


# TODO (Role 1): save the student's language choice (en/fr) in the users table
# def set_language(user_id, language): ...
