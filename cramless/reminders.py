"""
reminders.py - ROLE 4. Study reminders (#15).

Rule-based: if the student set a reminder time for today, that time has
passed, and they are still short of today's goal, a reminder is due.
It shows as a banner + browser notification on the dashboard, and
send_reminders() prints it for a scheduled job.
"""

from datetime import datetime

import planner
from database import get_connection

def todays_reminder_time(user_id):
    """Today's reminder time as 'HH:MM', or None if the students didn't set one."""
    conn = get_connection()
    row = conn.execute(
        "SELECT reminder_time FROM daily_goals WHERE user_id = ? AND weekday = ?",
        (user_id, datetime.now().weekday()),
    ).fetchone()
    conn.close()
    return row["reminder_time"] if row and row["reminder_time"] else None

def reminder_for(user_id, now=None):
    """The reminder message for this student right now, or None if none is due."""
    now = now or datetime.now()
    reminder_time = todays_reminder_time(user_id)
    if not reminder_time or now.strftime("%H:%M") < reminder_time:
        return None

    left = planner.todays_goal_minutes(user_id) - planner.minutes_studied_today(user_id)
    if left <= 0:
        return None

    plan = planner.build_daily_plan(user_id)
    if plan:
        return f"You've got {left} minutes left today. Start with {plan[0]['course_code']}!"
    return f"You've got {left} minutes left today. A short session still counts!"

def send_reminders():
    """Print a reminder for every student who is due one. Run on a schedule: python reminders.py"""
    conn = get_connection()
    users = conn.execute("SELECT id, email FROM users").fetchall()
    conn.close()
    for user in users:
        message = reminder_for(user["id"])
        if message:
            print(f"[reminder] {user['email']}: {message}")

if __name__=="__main__":
    send_reminders()