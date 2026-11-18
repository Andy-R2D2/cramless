"""
planner.py — ROLE 3. Exam dates, timetable, daily goals, daily plan, study time.
(functionalities #6 and #7)

Everything here is RULE-BASED (no AI): predictable and easy to explain.
"""

from datetime import date, datetime

from database import get_connection
import readiness

# Weights for the priority rules. Tune them as a team.
EXAM_WEIGHT = 3.0        # exam coming soon -> more time
UNREVIEWED_WEIGHT = 1.0  # each lecture not reviewed yet -> more time
READINESS_WEIGHT = 2.0   # low readiness score -> more time
EXAM_WINDOW_DAYS = 14    # exams further away than this don't count


# ---------------------------------------------------------------------------
# Setup: exams, timetable, goals
# ---------------------------------------------------------------------------

def add_exam(course_id, kind, exam_date, is_tentative=True):
    """Add a midterm or final. Tentative dates are fine (#6)."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO exams (course_id, kind, exam_date, is_tentative) VALUES (?, ?, ?, ?)",
        (course_id, kind, exam_date, int(is_tentative)),
    )
    conn.commit()
    conn.close()


def update_exam(exam_id, new_date, is_tentative):
    """Update an exam date and its tentative status when changes/announcements happen."""
    conn = get_connection()
    conn.execute(
        "UPDATE exams SET exam_date = ?, is_tentative = ? WHERE id = ?",
        (new_date, int(is_tentative), exam_id),
    )
    conn.commit()
    conn.close()


def get_exams(user_id):
    """Fetch all upcoming and past exams for a user's courses."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT exams.id, exams.course_id, exams.kind, exams.exam_date, exams.is_tentative, courses.code AS course_code
           FROM exams
           JOIN courses ON exams.course_id = courses.id
           WHERE courses.user_id = ?
           ORDER BY exams.exam_date ASC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def add_class_time(user_id, course_id, weekday, start_time, end_time):
    """Add a class to the weekly timetable after validating start < end time."""
    t_start = datetime.strptime(start_time, "%H:%M").time()
    t_end = datetime.strptime(end_time, "%H:%M").time()

    if t_start >= t_end:
        raise ValueError("Class start time must be strictly before end time.")

    conn = get_connection()
    conn.execute(
        "INSERT INTO class_times (user_id, course_id, weekday, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
        (user_id, course_id, weekday, start_time, end_time),
    )
    conn.commit()
    conn.close()


def get_timetable(user_id):
    """Fetch the user's weekly class schedule ordered by day and start time."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT class_times.id, class_times.weekday, class_times.start_time, class_times.end_time, courses.code AS course_code
           FROM class_times
           JOIN courses ON class_times.course_id = courses.id
           WHERE class_times.user_id = ?
           ORDER BY class_times.weekday ASC, class_times.start_time ASC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def set_daily_goal(user_id, weekday, hours, reminder_time=None):
    """Set the study goal for one weekday, e.g. Monday (0) = 3 hours (#7).
    Saving the same weekday again replaces the old goal."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO daily_goals (user_id, weekday, hours, reminder_time) VALUES (?, ?, ?, ?)
           ON CONFLICT (user_id, weekday) DO UPDATE SET hours = excluded.hours,
                                                         reminder_time = excluded.reminder_time""",
        (user_id, weekday, hours, reminder_time),
    )
    conn.commit()
    conn.close()


def get_daily_goals(user_id):
    """Return a dict mapping weekday (0=Mon .. 6=Sun) -> {'hours': float, 'reminder_time': str}."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT weekday, hours, reminder_time FROM daily_goals WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return {row["weekday"]: {"hours": row["hours"], "reminder_time": row["reminder_time"]} for row in rows}


def todays_goal_minutes(user_id):
    """Today's goal in minutes (0 if the student didn't set one for today)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT hours FROM daily_goals WHERE user_id = ? AND weekday = ?",
        (user_id, date.today().weekday()),
    ).fetchone()
    conn.close()
    return int(row["hours"] * 60) if row else 0


# ---------------------------------------------------------------------------
# Study time (timer + offline log)
# ---------------------------------------------------------------------------

def log_study(user_id, course_id, minutes, source):
    """Save study time. source = 'timer' (in-app timer) or 'offline' (manual log)."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO study_sessions (user_id, course_id, study_date, minutes, source) VALUES (?, ?, ?, ?, ?)",
        (user_id, course_id, date.today().isoformat(), minutes, source),
    )
    conn.commit()
    conn.close()


def minutes_studied_today(user_id):
    """Total minutes studied today, timer + offline."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(minutes), 0) AS total FROM study_sessions WHERE user_id = ? AND study_date = ?",
        (user_id, date.today().isoformat()),
    ).fetchone()
    conn.close()
    return row["total"]


# ---------------------------------------------------------------------------
# The daily plan (the main rule-based feature)
# ---------------------------------------------------------------------------

def priority_score(course_id, readiness_score):
    """
    Calculates a priority score for a given course.
    Higher priority scores yield a larger portion of today's study goal allocation.
    """
    conn = get_connection()
    today = date.today()

    exam_row = conn.execute(
        """SELECT exam_date FROM exams 
           WHERE course_id = ? AND exam_date >= ? 
           ORDER BY exam_date ASC LIMIT 1""",
        (course_id, today.isoformat()),
    ).fetchone()

    exam_part = 0.0
    if exam_row:
        exam_d = date.fromisoformat(exam_row["exam_date"])
        days_left = (exam_d - today).days
        if days_left <= EXAM_WINDOW_DAYS:
            exam_part = 1.0 - (days_left / EXAM_WINDOW_DAYS)

    unreviewed_row = conn.execute(
        "SELECT COUNT(*) AS count FROM lectures WHERE course_id = ? AND reviewed = 0",
        (course_id,),
    ).fetchone()
    unreviewed = unreviewed_row["count"] if unreviewed_row else 0
    conn.close()

    return (
        0.5
        + (EXAM_WEIGHT * exam_part)
        + (UNREVIEWED_WEIGHT * unreviewed)
        + (READINESS_WEIGHT * (1.0 - (readiness_score / 100.0)))
    )


def build_daily_plan(user_id):
    """
    Splits today's study goal across user courses weighted by priority score.
    Returns a sorted list of plans per course:
        [{"course_code": "CSCI 3230U", "minutes": 90, "lectures": ["Lecture 4", "Lecture 5"]}, ...]
    """
    goal = todays_goal_minutes(user_id)
    if goal <= 0:
        return []

    conn = get_connection()
    courses = conn.execute(
        "SELECT id, code, name FROM courses WHERE user_id = ?",
        (user_id,),
    ).fetchall()

    if not courses:
        conn.close()
        return []

    course_data = []
    total_score = 0.0

    for c in courses:
        c_id = c["id"]
        c_code = c["code"]
        r_score = readiness.course_score(c_id)
        p_score = priority_score(c_id, r_score)
        total_score += p_score

        course_data.append({
            "course_id": c_id,
            "course_code": c_code,
            "priority_score": p_score,
        })

    plan = []
    for c in course_data:
        raw_minutes = goal * (c["priority_score"] / total_score)
        allocated_minutes = int(round(raw_minutes / 15.0) * 15)

        if allocated_minutes <= 0:
            continue

        lectures_rows = conn.execute(
            """SELECT title FROM lectures 
               WHERE course_id = ? 
               ORDER BY reviewed ASC, number ASC 
               LIMIT 2""",
            (c["course_id"],),
        ).fetchall()

        lecture_titles = [row["title"] for row in lectures_rows]

        plan.append({
            "course_code": c["course_code"],
            "minutes": allocated_minutes,
            "lectures": lecture_titles,
            "_score": c["priority_score"],
        })

    conn.close()
    plan.sort(key=lambda x: x["_score"], reverse=True)
    for item in plan:
        item.pop("_score", None)

    return plan


def is_goal_realistic(user_id, weekday):
    """Warns (returns False) if total class commitments + planned study hours exceed 14 hours."""
    conn = get_connection()
    timetable_rows = conn.execute(
        "SELECT start_time, end_time FROM class_times WHERE user_id = ? AND weekday = ?",
        (user_id, weekday),
    ).fetchall()

    class_hours = 0.0
    for row in timetable_rows:
        t_start = datetime.strptime(row["start_time"], "%H:%M")
        t_end = datetime.strptime(row["end_time"], "%H:%M")
        class_hours += (t_end - t_start).total_seconds() / 3600.0

    goal_row = conn.execute(
        "SELECT hours FROM daily_goals WHERE user_id = ? AND weekday = ?",
        (user_id, weekday),
    ).fetchone()
    conn.close()

    study_hours = goal_row["hours"] if goal_row else 0.0
    return (class_hours + study_hours) <= 14.0