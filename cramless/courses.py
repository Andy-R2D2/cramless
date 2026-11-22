"""
courses.py — ROLE 2. Courses, lectures and flashcards (functionalities #4, #5).

All functions take user_id so a student only ever sees their own data.
"""

import os
from datetime import date

from database import get_connection

# Absolute path, so uploads work no matter which folder you run app.py from
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
MAX_UPLOAD_MB = 20


# ---------------------------------------------------------------------------
# Courses (#4) — issue #3: add, edit, delete
# ---------------------------------------------------------------------------

MAX_CODE_LENGTH = 20   # e.g. "CSCI 3230U"
MAX_NAME_LENGTH = 80   # e.g. "Web Development"


def get_courses(user_id):
    """Return all of the student's courses, sorted by course code."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM courses WHERE user_id = ? ORDER BY code", (user_id,)).fetchall()
    conn.close()
    return rows


def get_course(user_id, course_id):
    """Return one course, or None if it doesn't exist or belongs to another student."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM courses WHERE id = ? AND user_id = ?",  # user_id check = privacy
        (course_id, user_id),
    ).fetchone()
    conn.close()
    return row


def _clean_course_input(code, name):
    """
    Tidy up what the student typed and check it.
    Returns (code, name, error). error is None when everything is fine.
    """
    # Remove extra spaces; course codes are stored in capitals ("csci 3230u" -> "CSCI 3230U")
    code = " ".join((code or "").split()).upper()
    name = " ".join((name or "").split())

    if not code or not name:
        return code, name, "Please enter both a course code and a course name."
    if len(code) > MAX_CODE_LENGTH:
        return code, name, f"The course code can be at most {MAX_CODE_LENGTH} characters."
    if len(name) > MAX_NAME_LENGTH:
        return code, name, f"The course name can be at most {MAX_NAME_LENGTH} characters."
    return code, name, None


def _code_taken(conn, user_id, code, ignore_course_id=None):
    """True if this student already has a course with this code (ignoring one course when editing)."""
    row = conn.execute(
        "SELECT id FROM courses WHERE user_id = ? AND UPPER(code) = ? AND id != ?",
        (user_id, code.upper(), ignore_course_id or 0),
    ).fetchone()
    return row is not None


def add_course(user_id, code, name):
    """
    Add a course, e.g. add_course(1, 'CSCI 3230U', 'Web Development').
    Returns (course_id, error): course_id is None and error explains why if it failed.
    """
    code, name, error = _clean_course_input(code, name)
    if error:
        return None, error

    conn = get_connection()
    # Stop the student from adding the same course code twice
    if _code_taken(conn, user_id, code):
        conn.close()
        return None, f"You already added {code}."

    cursor = conn.execute(
        "INSERT INTO courses (user_id, code, name) VALUES (?, ?, ?)",
        (user_id, code, name),
    )
    conn.commit()
    course_id = cursor.lastrowid
    conn.close()
    return course_id, None


def rename_course(user_id, course_id, new_code, new_name):
    """
    Change a course's code and/or name.
    Returns an error message, or None if it worked.
    """
    code, name, error = _clean_course_input(new_code, new_name)
    if error:
        return error

    conn = get_connection()
    if _code_taken(conn, user_id, code, ignore_course_id=course_id):
        conn.close()
        return f"You already have a course called {code}."

    conn.execute(
        "UPDATE courses SET code = ?, name = ? WHERE id = ? AND user_id = ?",  # only your own course
        (code, name, course_id, user_id),
    )
    conn.commit()
    conn.close()
    return None


def delete_course(user_id, course_id):
    """
    Delete a course. Its lectures, summaries, flashcards, exams and study
    sessions are deleted too (ON DELETE CASCADE in database.py), and the
    uploaded lecture PDFs are removed from the uploads/ folder.
    """
    conn = get_connection()

    # Find the PDF files first, before the lecture rows disappear
    pdf_rows = conn.execute(
        """SELECT l.pdf_path FROM lectures l
           JOIN courses c ON l.course_id = c.id
           WHERE c.id = ? AND c.user_id = ?""",
        (course_id, user_id),
    ).fetchall()

    conn.execute("DELETE FROM courses WHERE id = ? AND user_id = ?", (course_id, user_id))
    conn.commit()
    conn.close()

    # Remove the files from disk (skip any that are already gone)
    for row in pdf_rows:
        if row["pdf_path"] and os.path.exists(row["pdf_path"]):
            os.remove(row["pdf_path"])


# ---------------------------------------------------------------------------
# Lectures (#5) — issue #4: upload resources + course page
# ---------------------------------------------------------------------------

MAX_TITLE_LENGTH = 120


def _clean_title(title, number):
    """Tidy the title; if the student leaves it empty, use 'Lecture <number>'."""
    title = " ".join((title or "").split())
    return title[:MAX_TITLE_LENGTH] if title else f"Lecture {number}"


def save_lecture(user_id, course_id, number, title, uploaded_file):
    """
    Check an uploaded PDF, save it in uploads/ and add the lecture to the database.
    `uploaded_file` is request.files["pdf"] from Flask.
    Returns (lecture_id, error): lecture_id is None and error explains why if it failed.
    (app.py then calls ai_generator.generate_for_lecture() to make the summary + flashcards.)
    """
    # 1. The course must exist and belong to this student
    if not get_course(user_id, course_id):
        return None, "Course not found."

    # 2. Lecture number: a whole number, 1 or more
    try:
        number = int(number)
    except (TypeError, ValueError):
        return None, "Please enter the lecture number (1, 2, 3 ...)."
    if number < 1:
        return None, "The lecture number must be 1 or more."

    # 3. A file was chosen, and it's a PDF
    if uploaded_file is None or not uploaded_file.filename:
        return None, "Please choose a PDF file."
    original_name = os.path.basename(uploaded_file.filename)  # keep only the file name, no folders
    if not original_name.lower().endswith(".pdf"):
        return None, "Only PDF files can be uploaded."
    # Real PDFs start with "%PDF": this catches files that were just renamed to .pdf
    if uploaded_file.stream.read(4) != b"%PDF":
        return None, "This file doesn't look like a real PDF."
    uploaded_file.stream.seek(0)  # go back to the start before saving

    # 4. Size limit (Flask also blocks huge uploads, see MAX_CONTENT_LENGTH in app.py)
    uploaded_file.stream.seek(0, os.SEEK_END)
    size_mb = uploaded_file.stream.tell() / (1024 * 1024)
    uploaded_file.stream.seek(0)
    if size_mb > MAX_UPLOAD_MB:
        return None, f"The file is too large ({size_mb:.1f} MB). The limit is {MAX_UPLOAD_MB} MB."

    conn = get_connection()
    # 5. Only one "Lecture 3" per course
    taken = conn.execute(
        "SELECT 1 FROM lectures WHERE course_id = ? AND number = ?", (course_id, number)
    ).fetchone()
    if taken:
        conn.close()
        return None, f"Lecture {number} is already uploaded. Delete it first to replace it."

    # 6. Save the file under a name we control (never trust the student's file name on disk)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    path = os.path.join(UPLOAD_FOLDER, f"course{course_id}_lecture{number}.pdf")
    uploaded_file.save(path)

    cursor = conn.execute(
        """INSERT INTO lectures (course_id, number, title, pdf_path, original_filename, uploaded_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (course_id, number, _clean_title(title, number), path, original_name, date.today().isoformat()),
    )
    conn.commit()
    lecture_id = cursor.lastrowid
    conn.close()
    return lecture_id, None


def get_lectures(course_id):
    """
    All lectures of a course, in order (Lecture 1, 2, 3 ...), each with
    has_summary (0/1) and card_count, so the course page can show their status.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT l.*,
                  (SELECT COUNT(*) FROM summaries s WHERE s.lecture_id = l.id) AS has_summary,
                  (SELECT COUNT(*) FROM flashcards f WHERE f.lecture_id = l.id) AS card_count
           FROM lectures l
           WHERE l.course_id = ?
           ORDER BY l.number""",
        (course_id,),
    ).fetchall()
    conn.close()
    return rows


def next_lecture_number(course_id):
    """The number to suggest in the upload form: one more than the highest so far."""
    conn = get_connection()
    row = conn.execute("SELECT MAX(number) AS top FROM lectures WHERE course_id = ?", (course_id,)).fetchone()
    conn.close()
    return (row["top"] or 0) + 1


def missing_lecture_numbers(lectures):
    """
    Gaps in the uploaded lectures, e.g. Lectures 1, 2, 4 uploaded -> [3].
    Students should upload every lecture from 1 to the current one.
    """
    uploaded = {lec["number"] for lec in lectures}
    highest = max(uploaded, default=0)
    return [n for n in range(1, highest) if n not in uploaded]


def get_lecture(user_id, lecture_id):
    """One lecture (with its course code), or None if it isn't this student's."""
    conn = get_connection()
    row = conn.execute(
        """SELECT l.*, c.code AS course_code, c.name AS course_name
           FROM lectures l JOIN courses c ON l.course_id = c.id
           WHERE l.id = ? AND c.user_id = ?""",
        (lecture_id, user_id),
    ).fetchone()
    conn.close()
    return row


def get_previous_and_next(lecture_id):
    """
    (previous_lecture, next_lecture) in the same course, for the
    "← Lecture 2" and "Lecture 4 →" buttons. None when there isn't one.
    """
    conn = get_connection()
    current = conn.execute("SELECT course_id, number FROM lectures WHERE id = ?", (lecture_id,)).fetchone()
    if current is None:
        conn.close()
        return None, None
    previous = conn.execute(
        """SELECT id, number, title FROM lectures
           WHERE course_id = ? AND number < ? ORDER BY number DESC LIMIT 1""",
        (current["course_id"], current["number"]),
    ).fetchone()
    following = conn.execute(
        """SELECT id, number, title FROM lectures
           WHERE course_id = ? AND number > ? ORDER BY number ASC LIMIT 1""",
        (current["course_id"], current["number"]),
    ).fetchone()
    conn.close()
    return previous, following


def delete_lecture(user_id, lecture_id):
    """
    Delete one lecture (its summary and flashcards go too, CASCADE) and its PDF.
    Returns the course id, so the page can go back to the course.
    """
    lecture = get_lecture(user_id, lecture_id)  # also checks it's this student's
    if lecture is None:
        return None
    conn = get_connection()
    conn.execute("DELETE FROM lectures WHERE id = ?", (lecture_id,))
    conn.commit()
    conn.close()
    if lecture["pdf_path"] and os.path.exists(lecture["pdf_path"]):
        os.remove(lecture["pdf_path"])
    return lecture["course_id"]


def get_summary(lecture_id):
    """The lecture's AI summary (key_concepts, explanation, examples), or None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM summaries WHERE lecture_id = ?", (lecture_id,)).fetchone()
    conn.close()
    return row


def mark_lecture_reviewed(lecture_id):
    """Set reviewed = 1 when the student studies the lecture (readiness 'coverage' uses it)."""
    conn = get_connection()
    conn.execute("UPDATE lectures SET reviewed = 1 WHERE id = ?", (lecture_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Flashcards — issue #5
# ---------------------------------------------------------------------------

def get_flashcards(lecture_id):
    """The lecture's flashcards (up to 10), in the order they were generated."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM flashcards WHERE lecture_id = ? ORDER BY id", (lecture_id,)).fetchall()
    conn.close()
    return rows


def _card_owner_check(conn, user_id, card_id):
    """True if this flashcard belongs to one of the student's courses."""
    row = conn.execute(
        """SELECT 1 FROM flashcards f
           JOIN lectures l ON f.lecture_id = l.id
           JOIN courses c ON l.course_id = c.id
           WHERE f.id = ? AND c.user_id = ?""",
        (card_id, user_id),
    ).fetchone()
    return row is not None


def record_answer(user_id, card_id, knew_it):
    """
    Called when the student clicks "Knew it" (knew_it=True) or "Didn't know".
    Updates the counters and the review date (Role 4 reads these for readiness).
    """
    column = "times_known" if knew_it else "times_missed"  # only these two values, never user text
    conn = get_connection()
    if _card_owner_check(conn, user_id, card_id):
        conn.execute(
            f"UPDATE flashcards SET {column} = {column} + 1, last_reviewed = ? WHERE id = ?",
            (date.today().isoformat(), card_id),
        )
        conn.commit()
    conn.close()


def edit_flashcard(user_id, card_id, question, answer):
    """Let the student fix a bad AI card. Returns an error message, or None if it worked."""
    question = (question or "").strip()
    answer = (answer or "").strip()
    if not question or not answer:
        return "A flashcard needs both a question and an answer."
    conn = get_connection()
    if not _card_owner_check(conn, user_id, card_id):
        conn.close()
        return "Flashcard not found."
    conn.execute("UPDATE flashcards SET question = ?, answer = ? WHERE id = ?", (question, answer, card_id))
    conn.commit()
    conn.close()
    return None


# ---------------------------------------------------------------------------
# Dashboard helpers (issue #2)
# ---------------------------------------------------------------------------

def get_course_cards(user_id):
    """
    Courses for the dashboard boxes, each with its number of lectures.
    Returns rows with: id, code, name, lecture_count
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.id, c.code, c.name, COUNT(l.id) AS lecture_count
           FROM courses c
           LEFT JOIN lectures l ON l.course_id = c.id   -- LEFT JOIN keeps courses with 0 lectures
           WHERE c.user_id = ?
           GROUP BY c.id
           ORDER BY c.code""",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_setup_progress(user_id):
    """
    Which of the 5 setup steps the student has done, for the
    "Getting started" checklist on the dashboard.
    Returns a dict like {"course": True, "lectures": False, ..., "done_count": 1, "all_done": False}
    """
    conn = get_connection()

    def has_rows(sql):
        # True if the query finds at least one row for this student
        return conn.execute(sql, (user_id,)).fetchone() is not None

    progress = {
        "course": has_rows("SELECT 1 FROM courses WHERE user_id = ? LIMIT 1"),
        "lectures": has_rows(
            """SELECT 1 FROM lectures l JOIN courses c ON l.course_id = c.id
               WHERE c.user_id = ? LIMIT 1"""
        ),
        "exams": has_rows(
            """SELECT 1 FROM exams e JOIN courses c ON e.course_id = c.id
               WHERE c.user_id = ? LIMIT 1"""
        ),
        # TODO (phase 5, with Teni): switch to the study timetable once it replaces class_times
        "timetable": has_rows("SELECT 1 FROM class_times WHERE user_id = ? LIMIT 1"),
        "goal": has_rows("SELECT 1 FROM daily_goals WHERE user_id = ? LIMIT 1"),
    }
    conn.close()

    # Count the finished steps; the checklist disappears when all 5 are done
    progress["done_count"] = sum(progress.values())
    progress["all_done"] = progress["done_count"] == 5
    return progress