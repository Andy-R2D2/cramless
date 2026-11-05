"""
planner.py — ROLE 3. Exam dates, timetable, daily goals, daily plan, study time.
(functionalities #6 and #7)

Everything here is RULE-BASED (no AI): predictable and easy to explain.
"""

from datetime import date

from database import get_connection

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
    """TODO (Role 3): change an exam date when the real one is announced."""
    pass


def add_class_time(user_id, course_id, weekday, start_time, end_time):
    """TODO (Role 3): add a class to the weekly timetable (check end > start)."""
    pass


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


def todays_goal_minutes(user_id):
    """Today's goal in minutes (0 if the student didn't set one for today)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT hours FROM daily_goals WHERE user_id = ? AND weekday = ?",
        (user_id, date.today().weekday()),  # Monday = 0
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
    One number per course: the higher it is, the more time it gets today.

    TODO (Role 3):
      days_left  = days until the course's next exam (ignore if > EXAM_WINDOW_DAYS)
      exam_part  = 1 - days_left / EXAM_WINDOW_DAYS       (0 if no exam soon)
      unreviewed = number of lectures with reviewed = 0
      return 0.5 + EXAM_WEIGHT * exam_part
                 + UNREVIEWED_WEIGHT * unreviewed
                 + READINESS_WEIGHT * (1 - readiness_score / 100)
    """
    return 1.0  # placeholder: every course is equal for now


def build_daily_plan(user_id):
    """
    Split today's goal between courses, highest priority first.
    Returns a list like:
        [{"course_code": "CSCI 3230U", "minutes": 90, "lectures": ["Lecture 4", "Lecture 5"]}, ...]

    TODO (Role 3):
      1. goal = todays_goal_minutes(user_id); return [] if 0
      2. for each course: score = priority_score(course_id, readiness.course_score(course_id))
      3. minutes = goal * score / total_of_all_scores  (round to the nearest 15)
      4. pick up to 2 lectures to study (not reviewed yet first)
      5. sort by score, highest first
    """
    return []


def is_goal_realistic(user_id, weekday):
    """TODO (Role 3, optional): warn if classes + study goal > 14 hours that day."""
    return True
