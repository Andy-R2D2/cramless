"""
courses.py — ROLE 2. Courses, lectures and flashcards (functionalities #4, #5).

All functions take user_id so a student only ever sees their own data.
"""

import os
from datetime import date

from database import get_connection

UPLOAD_FOLDER = "uploads"
MAX_UPLOAD_MB = 20


# ---------------------------------------------------------------------------
# Courses (#4)
# ---------------------------------------------------------------------------

def get_courses(user_id):
    """Return all of the student's courses, sorted by course code."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM courses WHERE user_id = ? ORDER BY code", (user_id,)).fetchall()
    conn.close()
    return rows


def add_course(user_id, code, name):
    """Add a course, e.g. add_course(1, 'CSCI 3230U', 'Web Development')."""
    # TODO (Role 2): stop the student from adding the same course code twice
    conn = get_connection()
    conn.execute("INSERT INTO courses (user_id, code, name) VALUES (?, ?, ?)", (user_id, code, name))
    conn.commit()
    conn.close()


def delete_course(user_id, course_id):
    """TODO (Role 2): delete a course (its lectures and cards go with it, CASCADE)."""
    pass


def rename_course(user_id, course_id, new_name):
    """TODO (Role 2): change a course's name."""
    pass


# ---------------------------------------------------------------------------
# Lectures (#5)
# ---------------------------------------------------------------------------

def save_lecture(course_id, number, title, uploaded_file):
    """
    Save an uploaded PDF in uploads/ and add the lecture to the database.
    `uploaded_file` is request.files["pdf"] from Flask.
    Returns the new lecture's id.

    TODO (Role 2):
      - refuse files that are not .pdf or bigger than MAX_UPLOAD_MB
      - after saving, call ai_generator.generate_for_lecture(lecture_id)
    """
    filename = f"course{course_id}_lecture{number}.pdf"
    path = os.path.join(UPLOAD_FOLDER, filename)
    uploaded_file.save(path)

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO lectures (course_id, number, title, pdf_path) VALUES (?, ?, ?, ?)",
        (course_id, number, title, path),
    )
    conn.commit()
    lecture_id = cursor.lastrowid
    conn.close()
    return lecture_id


def get_lectures(course_id):
    """All lectures of a course, in order (Lecture 1, 2, 3 ...)."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM lectures WHERE course_id = ? ORDER BY number", (course_id,)).fetchall()
    conn.close()
    return rows


def get_previous_and_next(lecture_id):
    """
    TODO (Role 2): return (previous_lecture, next_lecture) so the lecture page
    can show "← Lecture 2" and "Lecture 4 →" buttons. Use None when there isn't one.
    """
    return None, None


def get_summary(lecture_id):
    """TODO (Role 2): return the summary row for a lecture (or None)."""
    return None


def mark_lecture_reviewed(lecture_id):
    """TODO (Role 2): set reviewed = 1 (Role 4 uses this for the 'coverage' score)."""
    pass


# ---------------------------------------------------------------------------
# Flashcards
# ---------------------------------------------------------------------------

def get_flashcards(lecture_id):
    """TODO (Role 2): return the lecture's flashcards (up to 10)."""
    return []


def record_answer(card_id, knew_it):
    """
    Called when the student clicks "knew it" (knew_it=True) or "didn't know".
    Updates the counters and the review date (Role 4 reads these for readiness).
    """
    column = "times_known" if knew_it else "times_missed"
    conn = get_connection()
    conn.execute(
        f"UPDATE flashcards SET {column} = {column} + 1, last_reviewed = ? WHERE id = ?",
        (date.today().isoformat(), card_id),
    )
    conn.commit()
    conn.close()


def edit_flashcard(card_id, question, answer):
    """TODO (Role 2): let the student fix a bad AI card."""
    pass
