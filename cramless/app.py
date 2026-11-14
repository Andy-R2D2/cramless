"""
app.py — ROLE 1 (main file). Starts the website and connects every page.

Run the site with:
    python app.py
then open http://127.0.0.1:5000

Each route below calls a function from another role's file. Keep this file
short: the real logic lives in auth.py, courses.py, planner.py, readiness.py.
"""

import random

from flask import Flask, redirect, render_template, request, session, url_for

import auth
import courses
import planner
import readiness
from database import create_tables

app = Flask(__name__)
# Secret key signs the login session cookie. Change it before deploying!
app.secret_key = "dev-only-change-me"

# Create the tables automatically when the app starts
create_tables()


# ---------------------------------------------------------------------------
# English / French (functionality #9)
# ---------------------------------------------------------------------------

# TODO (Role 1): add every piece of text the HTML pages show, in both languages
TRANSLATIONS = {
    "en": {"welcome": "Study steady. Skip the cram.", 
           "register": "Register",
           "login": "Login",
           "email": "Email",
           "password": "Password",
           "confirmPassword": "Confirm Password",
           "existingUser": "Existing User",
           "newUser": "New User",
           "signIn": "Sign In",
           "signUp": "Sign Up",
           "dashboard": "Dashboard"},
    "fr": {"welcome": "Étudiez régulièrement. Oubliez le bachotage.",
           "register": "Registre",
           "login": "Connexion",
           "email": "E-mail",
           "password": "Mot de passe",
           "confirmPassword": "Confirmez le mot de passe",
           "existingUser": "Déjà utilisateur",
           "newUser": "Nouvel Utilisateur",
           "signIn": "Se Connecter",
           "signUp": "S'inscrire",
           "dashboard": "Tableau de bord"},
}

# Rule-based tips for the homepage (functionality #1)
TIPS = [
    "Short daily sessions beat one long cram the night before.",
    "Review yesterday's flashcards before starting a new lecture.",
    "Start with the course whose exam is closest.",
]


@app.context_processor
def add_text_to_templates():
    """Makes `t` (the text in the current language) available in every HTML page.
    In HTML: {{ t.welcome }}"""
    lang = session.get("language", "en")
    return {"t": TRANSLATIONS[lang], "lang": lang}


@app.route("/language/<lang>")
def switch_language(lang):
    """EN/FR button: save the choice and go back to the previous page."""
    if lang in TRANSLATIONS:
        session["language"] = lang

        user_id = current_user_id()
        if user_id:
            auth.set_language(user_id, lang)
    return redirect(request.referrer or (url_for("home")))


def current_user_id():
    """The logged-in student's id, or None if nobody is logged in."""
    return session.get("user_id")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    """Homepage with a sample readiness score and a random tip (#1)."""
    return render_template("home.html", sample_score=72, tip=random.choice(TIPS))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Create an account (#2).
    TODO (Role 1): create templates/register.html with an email + password form."""
    if request.method == "POST":

        password = request.form["password"]
        confirmPassword = request.form["confirmPassword"]
        if confirmPassword != password:
            return render_template("register.html", error="Passwords do not match.")

        
        user_id = auth.register_user(request.form["email"], request.form["password"])

        

        if user_id:
            lang = session.get("language", "en")# get the language from the session, default to English
            auth.set_language(user_id, lang)# save the language choice in the database

            return redirect(url_for("login"))
        return render_template("register.html", error="This email is already used.")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in (#2). TODO (Role 1): create templates/login.html."""
    if request.method == "POST":
        user_id = auth.check_login(request.form["email"], request.form["password"])
        if user_id:
            session["user_id"] = user_id
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Wrong email or password.")
    return render_template("login.html")

def set_language(user_id, lang):
    """Save the student's language choice (en/fr) in the users table."""
    auth.set_language(user_id, lang)


@app.route("/logout")
def logout():
    """Log out and go back to the homepage."""
    session.pop("user_id", None)
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    """Dashboard (#3): courses, today's plan, hours done vs goal, readiness.
    TODO (Role 1): create templates/dashboard.html and display these values."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    return render_template(
        "dashboard.html",
        courses=courses.get_courses(user_id),
        plan=planner.build_daily_plan(user_id),
        minutes_done=planner.minutes_studied_today(user_id),
        goal_minutes=planner.todays_goal_minutes(user_id),
        scores=readiness.all_scores(user_id),
    )

@app.route("/readiness")
def readiness_page():
    """Readiness score per course (#13): score, band and tip. Role 4."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    return render_template("readiness.html", scores=readiness.all_scores(user_id))

# TODO (Role 1, with each role): add the remaining pages here, for example:
#   /courses                     -> list + add courses           (Role 2)
#   /course/<id>                 -> lectures + upload form        (Role 2)
#   /lecture/<id>                -> summary + prev/next           (Role 2)
#   /lecture/<id>/flashcards     -> flashcard review              (Role 2)
#   /setup                       -> exams, timetable, daily goals (Role 3)
#   /plan                        -> today's plan + timer          (Role 3)
#   /readiness                   -> score per course              (Role 4)✅
# Each route should: check login, call ONE function from that role's file,
# then render_template(...).


if __name__ == "__main__":
    # debug=True reloads the server when you save a file
    app.run(debug=True)
