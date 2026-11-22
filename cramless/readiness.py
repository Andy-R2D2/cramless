"""
readiness.py — ROLE 4. Readiness score (#8) and reminders.

Readiness (0-100) = 0.35 x Mastery + 0.25 x Adherence + 0.15 x Consistency
                  + 0.15 x Freshness + 0.10 x Coverage

Each part is a percentage from 0 to 100. Everything here is rule-based.
"""

from database import get_connection
from datetime import date, timedelta

WEIGHTS = {
    "mastery": 0.35,      # % of flashcards known
    "adherence": 0.25,    # % of planned study time actually done this week
    "consistency": 0.15,  # % of the last 7 days with some studying
    "freshness": 0.15,    # % of cards reviewed in the last 7 days
    "coverage": 0.10,     # % of lectures reviewed at least once
}

TIPS = {
    "mastery": "Many cards are still unknown. Review the ones you missed.",
    "adherence": "You're behind on this week's hours. Try a short session today.",
    "consistency": "Spread your studying over more days.",
    "freshness": "Some cards haven't been reviewed in a while.",
    "coverage": "Some lectures haven't been opened yet. Start with the oldest.",
}


def percent(part, whole):
    """Safe percentage: 0 when there's nothing to count (avoids dividing by 0)."""
    return 100 * part / whole if whole else 0


# ---------------------------------------------------------------------------
# The 5 parts of the score
# ---------------------------------------------------------------------------

def mastery(course_id):
    """% of the course's flashcards marked as known (known more often than missed)."""
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) AS total,
                  SUM(CASE WHEN f.times_known > f.times_missed THEN 1 ELSE 0 END) AS known
           FROM flashcards f JOIN lectures l ON f.lecture_id = l.id
           WHERE l.course_id = ?""",
        (course_id,),
    ).fetchone()
    conn.close()
    return percent(row["known"] or 0, row["total"])


def coverage(course_id):
    """% of the course's lectures reviewed at least once."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS total, SUM(reviewed) AS done FROM lectures WHERE course_id = ?",
        (course_id,),
    ).fetchone()
    conn.close()
    return percent(row["done"] or 0, row["total"])


def adherence(course_id):
    """% of this week;s planned minutes actually studied for this course (max 100).
    Planned = daily goals for Monday...today, split evenly across the student's courses."""
    conn = get_connection()
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    course = conn.execute("SELECT user_id FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course:
        conn.close()
        return 0
    user_id = course["user_id"]

    n_courses = conn.execute(
        "SELECT COUNT(*) AS n FROM courses WHERE user_id = ?", (user_id,)
    ).fetchone()["n"]

    planned_hours = conn.execute(
        "SELECT COALESCE(SUM(hours), 0) AS h FROM daily_goals WHERE user_id = ? AND weekday <= ?",
        (user_id, today.weekday()),
    ).fetchone()["h"]
    planned_minutes = planned_hours * 60 / n_courses

    done = conn.execute(
        "SELECT COALESCE(SUM(minutes), 0) AS m FROM study_sessions WHERE course_id = ? AND study_date >= ?",
        (course_id, monday.isoformat()),
    ).fetchone()["m"]
    conn.close()
    return min(100, percent(done, planned_minutes))


def consistency(course_id):
    """% of the last7 days (today included) with at least one study session for this course."""
    since = date.today() - timedelta(days=6)
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT (DISTINCT study_date) AS days FROM study_sessions WHERE course_id = ? AND study_date >= ?",
        (course_id, since.isoformat()),
    ).fetchone()
    conn.close()
    return percent(row["days"], 7)


def freshness(course_id):
    """% of the course's flashcards reviewed in the last 7 days. Never-reviewed cards count as stale."""
    since = date.today() - timedelta(days=6)
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) AS total,
                  SUM(CASE WHEN f.last_reviewed >= ? THEN 1 ELSE 0 END) AS fresh
           FROM flashcards f JOIN lectures l ON f.lecture_id = l.id
           WHERE l.course_id = ?""",
        (since.isoformat(), course_id),
    ).fetchone()
    conn.close()
    return percent(row["fresh"] or 0, row["total"])


# ---------------------------------------------------------------------------
# Final score
# ---------------------------------------------------------------------------
def course_parts(course_id):
    """The 5 parts of the sore, each 0-100."""
    return {
        "mastery": mastery(course_id),
        "adherence": adherence(course_id),
        "consistency": consistency(course_id),
        "freshness": freshness(course_id),
        "coverage": coverage(course_id),
    }


def course_score(course_id):
    """The 0-100 readiness score for one course."""
    parts = course_parts(course_id)
    return round(sum(WEIGHTS[name] * value for name, value in parts.items()))


BANDS = [
    (80, "Exam ready", "You are in great shape. Keep short review sessions going so it stays that way."),
    (60, "On track", "Solid progress. Focus on the cards you still miss to push into exam-ready territory."),
    (40, "Getting there", "You've started, but gaps remain. Aim for a study session every day this week."),
    (20, "Needs attention", "You're behind where you want to be. Open the lectures you haven't reviewed yet."),
    (0, "Falling behind", "Time to start. Pick the course with the closest exam and do 25 minutes today.")
    
]
def band(score):
    """Label for a 20-point score band (0,19, 20-39, 40-59, 60-79, 80-100)."""
    for floor, label, _ in BANDS:
        if score >= floor:
            return label

def band_tip(score):
    """Human-written tip for the score's band (#14)."""
    for floor, _, tip in BANDS:
        if score >= floor:
            return tip


def weakest_tip(course_id):
    """Tip for the lowest of the 5 parts."""
    parts = course_parts(course_id)
    weakest = min(parts, key=parts.get)
    return TIPS[weakest]


def all_scores(user_id):
    """Score for each of the student's courses, for the dashboard."""
    conn = get_connection()
    courses = conn.execute("SELECT id, code FROM courses WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    results = []
    for course in courses:
        score = course_score(course["id"])
        results.append({
            "course_code": course["code"], 
            "score": score, "band": band(score), 
            "tip": weakest_tip(course["id"]), 
            "band_tip": band_tip(score)
        })
    return results


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------

def send_reminders():
    """
    TODO (Role 4):
      For each student whose reminder_time (daily_goals) is now:
        if planner.minutes_studied_today(user) < planner.todays_goal_minutes(user):
            send an encouraging message, e.g.
            "You've got 45 minutes left today. Start with CSCI 3230U!"
      Start by just print()-ing the message; add email later.
      Run it every 15 minutes: python readiness.py
    """
    pass


if __name__ == "__main__":
    send_reminders()
