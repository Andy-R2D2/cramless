# Cramless 📚

> **Study steady. Skip the cram.**

Cramless is a web app that helps university students study steadily instead of cramming before exams. Students add their courses and upload their lectures (Lecture 1 to the current one), and the app uses AI to turn each lecture into a **summary** (key concepts, in-depth explanation, real-life examples) and **up to 10 flashcards**, with proper formula support for math-heavy courses. Students enter their class timetable, tentative midterm/final dates and a daily study goal, and a **rule-based planner** builds a plan each day that splits their study hours across courses. Study time is tracked with a built-in timer or offline logs, a **0–100 readiness score** shows how prepared they are for each course, and a **reminder** is sent if they fall behind. The whole site works in **English and French**.

**Deadline:** a running project by **end of November 2026**.

---

## 👥 Team roles: pick one!

There are 4 of us, so the project is split into **4 roles**. Each role owns its own `.py` file(s), so we rarely edit the same file.

**Put your name in the table, open a PR that changes only this table, and we merge it.** First come, first served.

| Role | Files you own | Owner |
|---|---|---|
| **1. Website, accounts, dashboard & EN/FR** | `app.py`, `auth.py`, `templates/`, `static/` | Meron |
| **2. Courses, lectures & AI** | `courses.py`, `ai_generator.py` | _your name_ |
| **3. Planner: exams, timetable, goals, daily plan, timer** | `planner.py` | Teni|
| **4. Readiness score & reminders** | `readiness.py` | _your name_ |

`database.py` is **shared**: all the tables are already there. If you need a new column, tell the team first.

Every file has `TODO (Role X)` comments showing exactly what's left. Search for your role number to find them.

### Role 1: Website, accounts, dashboard & EN/FR
Functionalities **#1, #2, #3, #9**. Good fit for whoever likes **HTML / CSS**.
- [ ] Homepage with a sample readiness score + random tip *(starter done in `templates/home.html`)*
- [ ] `register.html` and `login.html` pages (the Python side is done in `auth.py`)
- [ ] `dashboard.html`: courses, today's plan, hours done vs goal, readiness per course
- [ ] Add a route in `app.py` for every page the other roles need
- [ ] Fill the `TRANSLATIONS` dictionary in `app.py` (English + French)
- [ ] CSS for the whole site, mobile-friendly
- [ ] To show formulas, add KaTeX to the lecture and flashcard pages (see https://katex.org/docs/autorender)

### Role 2: Courses, lectures & AI
Functionalities **#4, #5**. Good fit for whoever likes **Python + AI APIs**.
- [ ] Add / rename / delete courses (`courses.py`) *(add is done)*
- [ ] Upload lecture PDFs (Lecture 1 → current), check type and size *(saving is done)*
- [ ] Previous / next lecture
- [ ] PDF → images with PyMuPDF (`ai_generator.py`) *(done, test the DPI on a calculus lecture)*
- [ ] `generate_for_lecture()`: summary + up to 10 flashcards with formulas in LaTeX, saved to the database
- [ ] Flashcard review: "knew it / didn't know" *(saving the answer is done)*, edit a card

### Role 3: Planner
Functionalities **#6, #7**. Good fit for whoever likes **logic / algorithms**.
- [ ] Tentative midterm/final dates, editable (`planner.py`) *(add is done)*
- [ ] Weekly class timetable
- [ ] Daily study goal per weekday *(done)*
- [ ] **`priority_score()` and `build_daily_plan()`**: split today's goal between courses using exam dates, unreviewed lectures and readiness
- [ ] Study timer page (a simple JavaScript stopwatch in HTML) that calls `log_study(..., "timer")`
- [ ] Offline log ("I studied 1h") *(saving is done with `log_study(..., "offline")`)*

### Role 4: Readiness score & reminders
Functionality **#8** + reminders. Good fit for whoever likes **data / analytics**.
- [ ] Readiness score (`readiness.py`):
  `0.35 × Mastery + 0.25 × Adherence + 0.15 × Consistency + 0.15 × Freshness + 0.10 × Coverage`
  *(mastery and coverage are done, adherence, consistency and freshness are TODO)*
- [ ] Score bands (Exam ready / On track / Needs attention / Falling behind) *(done)*
- [ ] Tip for the weakest part of the score
- [ ] `send_reminders()`: message students who are behind on today's goal at their reminder time

> **AI is used in only one place:** summaries + flashcards (`ai_generator.py`). Everything else (plan, readiness, reminders, tips) is **rule-based**.

---

## 🛠️ Tech stack

| Part | Tool |
|---|---|
| Frontend | **HTML + CSS** (pages in `templates/`) |
| Backend | **Python + Flask** |
| Database | **SQLite** (one file, `cramless.db`, created automatically) |
| PDF → images | **PyMuPDF** |
| AI | **OpenAI API** (formulas in LaTeX) |

---

## 🚀 Getting started

```bash
# 1. Clone the repo
git clone <repo-url>
cd cramless

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file and add the OpenAI key (only Role 2 needs it at first)
cp .env.example .env          # Windows: copy .env.example .env

# 5. Run the website (the database is created automatically)
python app.py
```

Open http://127.0.0.1:5000.

> ⚠️ **Never commit `.env`** (it holds the OpenAI key). It's already in `.gitignore`.

---

## 📁 Project structure

```
cramless/
├── app.py            # Role 1: starts the site, every page (route) lives here
├── auth.py           # Role 1: register / log in
├── database.py       # SHARED: SQLite tables
├── courses.py        # Role 2: courses, lectures, flashcards
├── ai_generator.py   # Role 2: PDF -> images -> AI summary + flashcards
├── planner.py        # Role 3: exams, timetable, goals, daily plan, study time
├── readiness.py      # Role 4: readiness score + reminders
├── templates/        # HTML pages
├── static/           # CSS, images, JS
├── uploads/          # uploaded lecture PDFs (not pushed to GitHub)
└── requirements.txt
```

### How the files connect

```
app.py (pages) ──calls──▶ auth.py / courses.py / planner.py / readiness.py ──▶ database.py
courses.py ──after upload──▶ ai_generator.py
planner.py ──uses scores from──▶ readiness.py
```

**Rule of thumb:** HTML pages only display things. `app.py` only connects pages to functions. The real logic goes in your role's file.

---

## 🤝 Git workflow

1. **Never push straight to `main`.** Create a branch for your work:
   `git checkout -b role2/flashcards`
2. Commit small and often with clear messages:
   `git commit -m "Add previous/next lecture buttons"`
3. Push and open a **Pull Request**. At least one teammate reviews it before merging.
4. Before starting new work: `git checkout main && git pull`, then branch again.
5. Comment your code, so the others can follow it.

---

## ✅ Success criteria (rubric)

| # | Functionality | Done when… |
|---|---|---|
| 1 | Homepage | Shows a sample readiness score and a random tip |
| 2 | Login / register | Students sign up, log in, log out; each sees only their own data |
| 3 | Dashboard | Shows courses, today's plan, hours done vs goal, readiness per course |
| 4 | Courses | Students add, rename and delete courses |
| 5 | Lectures | PDFs from Lecture 1 → current upload; each has a summary and up to 10 flashcards; prev/next browsing works |
| 6 | Exam dates | Tentative midterm/final dates can be added and edited |
| 7 | Study goal + plan | Daily goal per weekday; the plan splits it across courses and names lectures; timer and offline log record time |
| 8 | Readiness score | 0–100 per course, band label, tip for the weakest part |
| 9 | English / French | The whole interface switches language; AI content is generated in the chosen language |
