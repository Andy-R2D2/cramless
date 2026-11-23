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

import ai_generator
import auth
import courses
import planner
import readiness
import reminders
from database import create_tables

app = Flask(__name__)
# Secret key signs the login session cookie. Change it before deploying!
app.secret_key = "dev-only-change-me"
# Refuse uploads bigger than the lecture PDF limit (+1 MB for the rest of the form)
app.config["MAX_CONTENT_LENGTH"] = (courses.MAX_UPLOAD_MB + 1) * 1024 * 1024

# Create the tables automatically when the app starts
create_tables()


# ---------------------------------------------------------------------------
# English / French (functionality #9)
# ---------------------------------------------------------------------------

# TODO (Role 1): add every piece of text the HTML pages show, in both languages
# Keys must be lowercase "en" and "fr": the code looks them up with session["language"]
TRANSLATIONS = {
    "en": {
        # --- Homepage, login, register (Meron) ---
        "welcome": "Study steady. Skip the cram.",
        "sampleReadiness": "Sample readiness",
        "setup": "Setup",
        "todaysPlanTimer": "Today's Plan & Timer",
        "register": "Register",
        "login": "Login",
        "logout": "Logout",
        "email": "Email",
        "password": "Password",
        "confirmPassword": "Confirm Password",
        "existingUser": "Existing User",
        "newUser": "New User",
        "signIn": "Sign In",
        "signUp": "Sign Up",
        "dashboard": "Dashboard",
        "tips": "Tip",
        # --- Dashboard (issue #2) ---
        "welcomeBack": "Welcome back!",
        "dashboardIntro": "Here's your study overview for today.",
        "gettingStarted": "Getting started",
        "stepCourse": "Add a course",
        "stepLectures": "Upload lectures",
        "stepExams": "Exam dates",
        "stepTimetable": "Study timetable",
        "stepGoal": "Daily goal",
        "todaysGoal": "Today's goal",
        "ofTodaysGoal": "of today's goal done",
        "noGoalToday": "No study goal set for today.",
        "setGoal": "Set one",
        "myCourses": "My courses",
        "addCourse": "Add course",
        "lecturesWord": "lectures",
        "readinessWord": "Readiness",
        "todaysPlan": "Today's study plan",
        "noLecturesYet": "No lectures uploaded yet",
        "noPlanYet": "Add a course and set today's goal to get a plan.",
        "start": "Start",
        "quickActions": "Quick actions",
        "startTimer": "Start study timer",
        "logOffline": "Log offline study",
        "editSetup": "Edit exams, timetable, goals",
        "tipOfDay": "Tip of the day",
        # --- Courses (issue #3) ---
        "courses": "Courses",
        "addCourseIntro": "Add one of the courses you're taking this term.",
        "courseCode": "Course code",
        "courseCodeHint": "As it appears on your timetable, e.g. CSCI 3230U",
        "courseName": "Course name",
        "cancel": "Cancel",
        "coursesIntro": "Edit or delete your courses.",
        "confirmDelete": "This also deletes all its lectures and flashcards. Delete",
        "delete": "Delete",
        "edit": "Edit",
        "save": "Save",
        "noCoursesYet": "No courses yet. Add your first one!",
        # --- Course page + upload (issue #4) ---
        "backToDashboard": "Back to dashboard",
        "uploadedLectures": "Uploaded lectures",
        "missingLectures": "Missing:",
        "lectureWord": "Lecture",
        "uploadedOn": "uploaded",
        "summaryReady": "Summary ready",
        "flashcardsWord": "flashcards",
        "summaryPending": "Summary not generated yet",
        "confirmDeleteLecture": "This also deletes its summary and flashcards. Delete lecture",
        "noLecturesHere": "No lectures yet. Upload Lecture 1 below.",
        "uploadLecture": "Upload a lecture",
        "lectureNumber": "Lecture #",
        "lectureTitle": "Title",
        "lectureTitleHint": "e.g. CSS Layout (optional)",
        "pdfFile": "PDF file",
        "pdfOnly": "PDF only, up to",
        "upload": "Upload",
        "summaryComingSoon": "The summary and flashcards for this lecture will appear here.",
        # --- Summary + flashcards (issue #5) ---
        "summaryFailed": "Summary failed",
        "noSummaryYet": "No summary or flashcards for this lecture yet.",
        "generate": "Generate summary and flashcards",
        "generating": "Generating... (up to a minute)",
        "summaryTab": "Summary",
        "flashcardsTab": "Flashcards",
        "keyConcepts": "Key concepts",
        "inDepthExplanation": "In-depth explanation",
        "realLifeExamples": "Real-life examples",
        "aiExample": "AI example",
        "practiseFlashcards": "Practise with flashcards",
        "regenerate": "Regenerate",
        "confirmRegenerate": "Make a new summary and flashcards? Your current ones (and your progress on them) will be replaced.",
        "noFlashcards": "No flashcards for this lecture.",
        "cardWord": "Card",
        "showAnswer": "Show answer",
        "knewIt": "Knew it",
        "didntKnow": "Didn't know",
        "editCard": "Edit card",
        "questionWord": "Question",
        "answerWord": "Answer",
        "deckDone": "You've gone through all the cards!",
        "masteredCount": "Cards you know:",
        "reviewAgain": "Review again",
    },
    "fr": {
        # --- Accueil, connexion, inscription (Meron) ---
        "welcome": "Étudiez régulièrement. Oubliez le bachotage.",
        "sampleReadiness": "Préparation des échantillons",
        "setup": "Configurer",
        "todaysPlanTimer": "Plan et minuterie de la journée",
        "register": "Registre",
        "login": "Connexion",
        "logout": "Déconnexion ",
        "email": "E-mail",
        "password": "Mot de passe",
        "confirmPassword": "Confirmez le mot de passe",
        "existingUser": "Déjà utilisateur",
        "newUser": "Nouvel Utilisateur",
        "signIn": "Se Connecter",
        "signUp": "S'inscrire",
        "dashboard": "Tableau de bord",
        "tips": "Pourboires",
        # --- Tableau de bord (issue #2) ---
        "welcomeBack": "Bon retour !",
        "dashboardIntro": "Voici votre aperçu d'étude pour aujourd'hui.",
        "gettingStarted": "Pour commencer",
        "stepCourse": "Ajouter un cours",
        "stepLectures": "Téléverser des cours",
        "stepExams": "Dates d'examen",
        "stepTimetable": "Horaire d'étude",
        "stepGoal": "Objectif quotidien",
        "todaysGoal": "Objectif du jour",
        "ofTodaysGoal": "de l'objectif du jour atteint",
        "noGoalToday": "Aucun objectif d'étude pour aujourd'hui.",
        "setGoal": "En définir un",
        "myCourses": "Mes cours",
        "addCourse": "Ajouter un cours",
        "lecturesWord": "cours magistraux",
        "readinessWord": "Préparation",
        "todaysPlan": "Plan d'étude du jour",
        "noLecturesYet": "Aucun cours téléversé",
        "noPlanYet": "Ajoutez un cours et un objectif du jour pour obtenir un plan.",
        "start": "Commencer",
        "quickActions": "Actions rapides",
        "startTimer": "Lancer le minuteur",
        "logOffline": "Noter une étude hors ligne",
        "editSetup": "Modifier examens, horaire, objectifs",
        "tipOfDay": "Astuce du jour",
        # --- Cours (issue #3) ---
        "courses": "Cours",
        "addCourseIntro": "Ajoutez un des cours que vous suivez ce trimestre.",
        "courseCode": "Code du cours",
        "courseCodeHint": "Comme sur votre horaire, ex. CSCI 3230U",
        "courseName": "Nom du cours",
        "cancel": "Annuler",
        "coursesIntro": "Modifiez ou supprimez vos cours.",
        "confirmDelete": "Cela supprime aussi tous ses cours magistraux et cartes mémoire. Supprimer",
        "delete": "Supprimer",
        "edit": "Modifier",
        "save": "Enregistrer",
        "noCoursesYet": "Aucun cours pour l'instant. Ajoutez le premier !",
        # --- Page du cours + téléversement (issue #4) ---
        "backToDashboard": "Retour au tableau de bord",
        "uploadedLectures": "Cours téléversés",
        "missingLectures": "Manquants :",
        "lectureWord": "Cours",
        "uploadedOn": "téléversé le",
        "summaryReady": "Résumé prêt",
        "flashcardsWord": "cartes mémoire",
        "summaryPending": "Résumé pas encore généré",
        "confirmDeleteLecture": "Cela supprime aussi son résumé et ses cartes mémoire. Supprimer le cours",
        "noLecturesHere": "Aucun cours pour l'instant. Téléversez le cours 1 ci-dessous.",
        "uploadLecture": "Téléverser un cours",
        "lectureNumber": "Cours n°",
        "lectureTitle": "Titre",
        "lectureTitleHint": "ex. Mise en page CSS (facultatif)",
        "pdfFile": "Fichier PDF",
        "pdfOnly": "PDF seulement, jusqu'à",
        "upload": "Téléverser",
        "summaryComingSoon": "Le résumé et les cartes mémoire de ce cours apparaîtront ici.",
        # --- Résumé + cartes mémoire (issue #5) ---
        "summaryFailed": "Échec du résumé",
        "noSummaryYet": "Pas encore de résumé ni de cartes mémoire pour ce cours.",
        "generate": "Générer le résumé et les cartes mémoire",
        "generating": "Génération en cours... (jusqu'à une minute)",
        "summaryTab": "Résumé",
        "flashcardsTab": "Cartes mémoire",
        "keyConcepts": "Concepts clés",
        "inDepthExplanation": "Explication détaillée",
        "realLifeExamples": "Exemples concrets",
        "aiExample": "Exemple IA",
        "practiseFlashcards": "S'entraîner avec les cartes",
        "regenerate": "Régénérer",
        "confirmRegenerate": "Créer un nouveau résumé et de nouvelles cartes ? Les actuels (et votre progression) seront remplacés.",
        "noFlashcards": "Aucune carte mémoire pour ce cours.",
        "cardWord": "Carte",
        "showAnswer": "Voir la réponse",
        "knewIt": "Je savais",
        "didntKnow": "Je ne savais pas",
        "editCard": "Modifier la carte",
        "questionWord": "Question",
        "answerWord": "Réponse",
        "deckDone": "Vous avez vu toutes les cartes !",
        "masteredCount": "Cartes maîtrisées :",
        "reviewAgain": "Revoir",
    },
}

# Rule-based tips for the homepage (functionality #1)
TIPS = {
    "en": [
        "Short daily sessions beat one long cram the night before.",
        "Review yesterday's flashcards before starting a new lecture.",
        "Start with the course whose exam is closest."
    ],

    "fr": [
        "De courtes séances quotidiennes valent mieux qu’une longue séance de bachotage la veille.",
        "Révisez les cartes-mémoire d’hier avant de commencer un nouveau cours.",
        "Commencez par le cours dont l’examen est le plus proche."
    ]
}
    


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
    lang = session.get("language", "en")
    return render_template("home.html", sample_score=72, tip=random.choice(TIPS[lang]))


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
            lang = session.get("language", "en")  # get the language from the session, default to English
            auth.set_language(user_id, lang)      # save the language choice in the database

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

@app.route("/policy")
def policy():
    """Content & Privacy Policy (#16). Role 4."""
    return render_template("policy.html")

@app.route("/dashboard")
def dashboard():
    """Dashboard (issue #2): setup checklist, today's goal, course boxes
    with "+ Add course", today's plan, quick actions and a tip."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))

    lang = session.get("language", "en")

    # Readiness scores keyed by course code, so each course box can find its own score
    score_by_code = {s["course_code"]: s for s in readiness.all_scores(user_id)}

    return render_template(
        "dashboard.html",
        checklist=courses.get_setup_progress(user_id),   # 5 setup steps
        course_cards=courses.get_course_cards(user_id),  # courses + lecture counts
        score_by_code=score_by_code,
        plan=planner.build_daily_plan(user_id),
        minutes_done=planner.minutes_studied_today(user_id),
        goal_minutes=planner.todays_goal_minutes(user_id),
        tip=random.choice(TIPS[lang]),
        reminder=reminders.reminder_for(user_id),
    )


@app.route("/setup", methods=["GET", "POST"])
def setup():
    """Exams, weekly class timetable, and daily study goals (Role 3)."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))

    error = None
    warning = None
    message = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_exam":
            planner.add_exam(
                int(request.form["course_id"]),
                request.form["kind"],
                request.form["exam_date"],
                "is_tentative" in request.form,
            )
            message = "Exam added."

        elif action == "update_exam":
            planner.update_exam(
                int(request.form["exam_id"]),
                request.form["new_date"],
                "is_tentative" in request.form,
            )
            message = "Exam updated."

        elif action == "add_class":
            weekday = int(request.form["weekday"])
            try:
                planner.add_class_time(
                    user_id,
                    int(request.form["course_id"]),
                    weekday,
                    request.form["start_time"],
                    request.form["end_time"],
                )
                message = "Class added to timetable."
                if not planner.is_goal_realistic(user_id, weekday):
                    warning = "Total class + study time for this day exceeds 14 hours."
            except ValueError as e:
                error = str(e)

        elif action == "set_goal":
            weekday = int(request.form["weekday"])
            hours = float(request.form["hours"])
            reminder = request.form.get("reminder_time") or None
            planner.set_daily_goal(user_id, weekday, hours, reminder)
            message = "Daily goal saved."
            if not planner.is_goal_realistic(user_id, weekday):
                warning = "Total class + study time for this day exceeds 14 hours."

    return render_template(
        "setup.html",
        courses=courses.get_courses(user_id),
        exams=planner.get_exams(user_id),
        timetable=planner.get_timetable(user_id),
        goals=planner.get_daily_goals(user_id),
        error=error,
        warning=warning,
        message=message,
    )


@app.route("/plan", methods=["GET", "POST"])
def plan():
    """Today's study plan, JS stopwatch timer, and offline study log (Role 3)."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))

    message = None
    if request.method == "POST":
        course_id = int(request.form["course_id"])
        minutes = int(request.form["minutes"])
        source = request.form.get("source", "offline")
        if minutes > 0:
            planner.log_study(user_id, course_id, minutes, source)
            message = f"Logged {minutes} minutes ({source})."

    return render_template(
        "plan.html",
        courses=courses.get_courses(user_id),
        daily_plan=planner.build_daily_plan(user_id),
        minutes_done=planner.minutes_studied_today(user_id),
        goal_minutes=planner.todays_goal_minutes(user_id),
        message=message,
    )


@app.route("/courses")
def courses_page():
    """My courses (issue #3): list of courses with edit and delete.
    Named courses_page so the "Courses" link already written in base.html works."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    return render_template(
        "courses.html",
        course_cards=courses.get_course_cards(user_id),
        error=request.args.get("error"),      # set by edit_course below when something fails
        message=request.args.get("message"),
    )


@app.route("/courses/add", methods=["GET", "POST"])
def add_course():
    """Add course page (issue #3). The "+ Add course" box on the dashboard links here."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        course_id, error = courses.add_course(user_id, request.form.get("code"), request.form.get("name"))
        if error:
            # Show the form again, keeping what the student typed
            return render_template("add_course.html", error=error,
                                   code=request.form.get("code", ""), name=request.form.get("name", ""))
        # Back to the dashboard, where the new course box appears before "+ Add course"
        return redirect(url_for("dashboard"))

    return render_template("add_course.html", code="", name="")


@app.route("/courses/<int:course_id>/edit", methods=["POST"])
def edit_course(course_id):
    """Save a course's new code/name from the My courses page."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    error = courses.rename_course(user_id, course_id, request.form.get("code"), request.form.get("name"))
    if error:
        return redirect(url_for("courses_page", error=error))
    return redirect(url_for("courses_page", message="Course updated."))


@app.route("/courses/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    """Delete a course (POST only, so a link or a page refresh can't delete by accident)."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    courses.delete_course(user_id, course_id)
    return redirect(url_for("courses_page", message="Course deleted."))


@app.route("/course/<int:course_id>")
def course_page(course_id):
    """Course page (issue #4): uploaded lectures (names only) + upload form.
    The course boxes on the dashboard link here."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    course = courses.get_course(user_id, course_id)
    if course is None:
        return redirect(url_for("dashboard"))  # not found, or another student's course

    lectures = courses.get_lectures(course_id)
    score = readiness.course_score(course_id)
    return render_template(
        "course.html",
        course=course,
        lectures=lectures,
        missing=courses.missing_lecture_numbers(lectures),
        next_number=courses.next_lecture_number(course_id),
        score=score,
        band=readiness.band(score),
        max_mb=courses.MAX_UPLOAD_MB,
        error=request.args.get("error"),
        message=request.args.get("message"),
    )


@app.route("/course/<int:course_id>/upload", methods=["POST"])
def upload_lecture(course_id):
    """Upload form on the course page."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    lecture_id, error = courses.save_lecture(
        user_id, course_id,
        request.form.get("number"), request.form.get("title"), request.files.get("pdf"),
    )
    if error:
        return redirect(url_for("course_page", course_id=course_id, error=error))

    # Make the summary + flashcards right away, in the student's language (takes 20-60 s).
    # If it fails, the lecture is still saved and the lecture page shows the error + a retry button.
    ok, ai_error = ai_generator.generate_for_lecture(lecture_id, session.get("language", "en"))
    if not ok:
        return redirect(url_for("lecture_page", lecture_id=lecture_id,
                                error=f"Lecture uploaded, but the summary couldn't be generated: {ai_error}"))
    return redirect(url_for("lecture_page", lecture_id=lecture_id, message="Lecture uploaded. Summary and flashcards ready!"))


@app.route("/lecture/<int:lecture_id>")
def lecture_page(lecture_id):
    """Lecture page (issue #5): two options, Summary or Flashcards, + previous / next.
    ?tab=summary (default) or ?tab=flashcards, and ?card=N for the flashcard being shown."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    lecture = courses.get_lecture(user_id, lecture_id)
    if lecture is None:
        return redirect(url_for("dashboard"))

    summary = courses.get_summary(lecture_id)
    cards = courses.get_flashcards(lecture_id)
    if summary:
        courses.mark_lecture_reviewed(lecture_id)  # studying it counts for readiness "coverage"

    tab = "flashcards" if request.args.get("tab") == "flashcards" else "summary"
    # Which card to show (0 = first). Past the last card = the "done" screen.
    card_index = max(0, request.args.get("card", default=0, type=int))
    previous, following = courses.get_previous_and_next(lecture_id)
    return render_template(
        "lecture.html",
        lecture=lecture, summary=summary, cards=cards,
        tab=tab, card_index=card_index,
        previous=previous, following=following,
        error=request.args.get("error"), message=request.args.get("message"),
    )


@app.route("/lecture/<int:lecture_id>/generate", methods=["POST"])
def generate_lecture(lecture_id):
    """'Generate' / 'Regenerate' button: run the AI pipeline for this lecture."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    if courses.get_lecture(user_id, lecture_id) is None:
        return redirect(url_for("dashboard"))
    ok, error = ai_generator.generate_for_lecture(lecture_id, session.get("language", "en"))
    if not ok:
        return redirect(url_for("lecture_page", lecture_id=lecture_id, error=error))
    return redirect(url_for("lecture_page", lecture_id=lecture_id, message="Summary and flashcards generated."))


@app.route("/flashcard/<int:card_id>/answer", methods=["POST"])
def answer_card(card_id):
    """'Knew it' / 'Didn't know' buttons: save the answer, then show the next card."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    courses.record_answer(user_id, card_id, request.form.get("result") == "known")
    return redirect(url_for(
        "lecture_page",
        lecture_id=request.form.get("lecture_id", type=int),
        tab="flashcards",
        card=request.form.get("next_card", default=0, type=int),
    ))


@app.route("/flashcard/<int:card_id>/edit", methods=["POST"])
def edit_card(card_id):
    """Fix a bad AI card (the "Edit card" form under each flashcard)."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    error = courses.edit_flashcard(user_id, card_id, request.form.get("question"), request.form.get("answer"))
    return redirect(url_for(
        "lecture_page",
        lecture_id=request.form.get("lecture_id", type=int),
        tab="flashcards",
        card=request.form.get("card", default=0, type=int),
        error=error,
        message=None if error else "Flashcard updated.",
    ))


@app.route("/lecture/<int:lecture_id>/delete", methods=["POST"])
def delete_lecture(lecture_id):
    """Delete a lecture from the course page (POST only, like delete_course)."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    course_id = courses.delete_lecture(user_id, lecture_id)
    if course_id is None:
        return redirect(url_for("dashboard"))
    return redirect(url_for("course_page", course_id=course_id, message="Lecture deleted."))


@app.errorhandler(413)
def file_too_large(error):
    """Flask stops uploads bigger than MAX_CONTENT_LENGTH before our code runs:
    send the student back to the course page with a clear message."""
    course_id = (request.view_args or {}).get("course_id")
    message = f"The file is too large. The limit is {courses.MAX_UPLOAD_MB} MB."
    if course_id:
        return redirect(url_for("course_page", course_id=course_id, error=message))
    return redirect(url_for("dashboard"))

@app.route("/readiness")
def readiness_page():
    """Readiness score per course (#13): score, band and tip. Role 4."""
    user_id = current_user_id()
    if not user_id:
        return redirect(url_for("login"))
    return render_template("readiness.html", scores=readiness.all_scores(user_id))

# Pages done so far (all routes above):
#   /courses, /courses/add, /course/<id>, /lecture/<id>    (Role 2) ✅
#   /setup, /plan                                           (Role 3) ✅
#   /readiness, /policy                                     (Role 4) ✅
# Each route should: check login, call ONE function from that role's file,
# then render_template(...).


if __name__ == "__main__":
    # debug=True reloads the server when you save a file
    app.run(debug=True)