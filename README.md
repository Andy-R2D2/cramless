# Cramless 📚

> Study steady. Skip the cram.

**Cramless** is a web app that helps university students study steadily through the semester instead of cramming before exams. Students add their courses and upload lecture PDFs; the app uses AI to turn each lecture into a summary and a set of flashcards, builds a daily study plan around upcoming exams, tracks study time, and gives every course a 0–100 **readiness score** so students always know where they stand.

The whole site works in **English and French**.

🎥 **Demo video:** [Sprint Demo (Google Drive)](https://drive.google.com/drive/u/0/folders/1Q08_Qq6nBzLON6WaNI0lvwsGfpBVI_O2)

**Status:** ✅ Completed (November 2026 CS club project sprint)

---

## ✨ Features

| Feature | What it does |
|---|---|
| **Accounts** | Sign up, log in and log out; each student sees only their own data |
| **Dashboard** | Courses, today's plan, hours studied vs. goal, and readiness per course at a glance |
| **Courses & lectures** | Add, rename and delete courses; upload lecture PDFs in order (Lecture 1 → current) and browse them with previous/next |
| **AI summaries** | Each lecture becomes a summary with key concepts, an in-depth explanation and real-life examples |
| **AI flashcards** | Up to 10 flashcards per lecture, with math formulas rendered properly (LaTeX + KaTeX) |
| **Flashcard review** | Mark each card "knew it" / "didn't know"; results feed into the readiness score; cards can be edited |
| **Exam dates** | Add and edit tentative midterm and final dates per course |
| **Timetable & daily goal** | Weekly class timetable plus a study-hour goal for each weekday |
| **Daily planner** | A rule-based planner splits today's goal across courses based on exam dates, unreviewed lectures and readiness |
| **Study tracking** | Built-in stopwatch timer, or log offline study ("I studied 1h") |
| **Readiness score** | 0–100 score per course, with a status band and a tip for the weakest area |
| **Reminders** | Students who fall behind on today's goal get a reminder |
| **English / French** | The interface switches language, and AI content is generated in the chosen language |

---

## 📊 How the readiness score works

Each course gets a score from 0 to 100:

```
Readiness = 0.35 × Mastery + 0.25 × Adherence + 0.15 × Consistency + 0.15 × Freshness + 0.10 × Coverage
```

| Component | Meaning |
|---|---|
| **Mastery** | How well the student knows the flashcards |
| **Adherence** | How closely they follow their daily study goal |
| **Consistency** | How regularly they study (steady vs. last-minute) |
| **Freshness** | How recently the material was reviewed |
| **Coverage** | How many uploaded lectures have been reviewed |

The score maps to a band: **Exam ready**, **On track**, **Needs attention** or **Falling behind**, and the app shows a tip for the weakest component.

AI is used in only one place: lecture summaries and flashcards. Everything else (planner, readiness, reminders, tips) is rule-based, so it is fast, predictable and free to run.

---

## 🛠️ Tech stack

| Part | Tool |
|---|---|
| Frontend | HTML + CSS (Jinja templates), KaTeX for formulas |
| Backend | Python + Flask |
| Database | SQLite (`cramless.db`, created automatically) |
| PDF processing | PyMuPDF (PDF → images) |
| AI | OpenAI API |

---

## 🚀 Getting started

```bash
# 1. Clone the repo
git clone https://github.com/Andy-R2D2/cramless.git
cd cramless

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file and add your OpenAI API key
cp .env.example .env          # Windows: copy .env.example .env

# 5. Run the app (the database is created automatically)
python app.py
```

Then open <http://127.0.0.1:5000>.

> ⚠️ Never commit `.env`; it holds your OpenAI key and is already in `.gitignore`.

---

## 📁 Project structure

```
cramless/
├── app.py            # Starts the site; every page (route) lives here
├── auth.py           # Register / log in / log out
├── database.py       # SQLite tables (shared)
├── courses.py        # Courses, lectures, flashcards
├── ai_generator.py   # PDF → images → AI summary + flashcards
├── planner.py        # Exams, timetable, goals, daily plan, study time
├── readiness.py      # Readiness score, bands, tips, reminders
├── templates/        # HTML pages
├── static/           # CSS, images, JS
├── uploads/          # Uploaded lecture PDFs (not pushed to GitHub)
└── requirements.txt
```

### How the files connect

```
app.py (pages) ──calls──▶ auth.py / courses.py / planner.py / readiness.py ──▶ database.py
courses.py ──after upload──▶ ai_generator.py
planner.py ──uses scores from──▶ readiness.py
```

HTML pages only display things, `app.py` connects pages to functions, and the real logic lives in each module.

---

## 👥 Team

| Member | GitHub | Role |
|---|---|---|
| Meron Daniel | [@MeronDaniel](https://github.com/MeronDaniel) | Website, accounts, dashboard & EN/FR (`app.py`, `auth.py`, `templates/`, `static/`) |
| Andy Donghakia | [@Andy-R2D2](https://github.com/Andy-R2D2) | Courses, lectures & AI summaries/flashcards (`courses.py`, `ai_generator.py`) |
| Teni | [@Teninator](https://github.com/Teninator) | Planner: exams, timetable, goals, daily plan, study timer (`planner.py`) |
| Raihan Mosharrof | [@Raihan-Mosharrof](https://github.com/Raihan-Mosharrof) | Readiness score & reminders (`readiness.py`) |

Built with a branch-per-feature workflow: every change went through a pull request reviewed by a teammate before merging into `main`.
