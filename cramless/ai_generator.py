"""
ai_generator.py — ROLE 2 (issue #5: Flashcard generation).
Lecture PDF -> summary + up to 10 flashcards.

This is the ONLY place we use AI. Results are saved in the database once,
so we don't pay for the same lecture twice (except with "Regenerate").

Steps:
  1. PDF pages -> images (PyMuPDF), so math formulas are read correctly
  2. Send the images to the OpenAI API (in batches), ask for JSON
  3. Check the JSON, then save the summary and flashcards in the database

Put your key in a .env file next to app.py:   OPENAI_API_KEY=sk-...
"""

import base64
import json
import math
import os

from dotenv import load_dotenv

from database import get_connection

# Read OPENAI_API_KEY / OPENAI_MODEL from the .env file next to this file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

MAX_FLASHCARDS = 10   # cards per lecture
PAGES_PER_CALL = 12   # long lectures are sent in batches of 12 pages
MAX_PAGES = 60        # safety limit, so one huge PDF can't use up our credits
DPI = 150             # image sharpness: try 200 if small exponents come out wrong

PROMPT = """You are a study assistant for university students.
Using ONLY the lecture slides in these images, return a JSON object with exactly these keys:
  "key_concepts": the main concepts, one per line, each line starting with "- " (string)
  "explanation": an in-depth explanation of each concept, in clear paragraphs (string)
  "examples": one real-life example per concept, in short paragraphs (string)
  "flashcards": a list of up to {max_cards} objects like {{"question": "...", "answer": "..."}}
Rules:
- Write every formula in LaTeX: $...$ inline, $$...$$ on its own line.
- Do not add topics that are not in the slides.
- Questions must be answerable from the slides; answers short (1-3 sentences).
- Respond in {language}."""


class GenerationError(Exception):
    """A problem we can explain to the student (shown on the lecture page)."""


# ---------------------------------------------------------------------------
# Step 1: PDF -> images
# ---------------------------------------------------------------------------

def pdf_to_images(pdf_path, dpi=DPI):
    """Turn each PDF page into a PNG image (bytes), up to MAX_PAGES pages."""
    import fitz  # PyMuPDF. Imported here so the rest of the site works even if it's missing

    images = []
    with fitz.open(pdf_path) as doc:
        for page_number, page in enumerate(doc):
            if page_number >= MAX_PAGES:
                break
            images.append(page.get_pixmap(dpi=dpi).tobytes("png"))
    if not images:
        raise GenerationError("This PDF has no pages.")
    return images


def batch_pages(images, size=PAGES_PER_CALL):
    """Split the pages into batches, e.g. 30 pages -> 12 + 12 + 6."""
    return [images[i:i + size] for i in range(0, len(images), size)]


# ---------------------------------------------------------------------------
# Step 2: ask the AI
# ---------------------------------------------------------------------------

def ask_ai(images, language="English", max_cards=MAX_FLASHCARDS):
    """Send one batch of page images to OpenAI and return the answer as a Python dict."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise GenerationError("No OpenAI API key found. Add OPENAI_API_KEY to the .env file.")

    from openai import OpenAI  # imported here so the site still runs without the package

    client = OpenAI(api_key=api_key)

    # The message = the instructions + every page as an image
    content = [{"type": "text", "text": PROMPT.format(max_cards=max_cards, language=language)}]
    for png in images:
        b64 = base64.b64encode(png).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},  # forces valid JSON
        messages=[{"role": "user", "content": content}],
    )
    try:
        return json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, TypeError):
        raise GenerationError("The AI's answer wasn't valid JSON. Try Regenerate.")


# ---------------------------------------------------------------------------
# Step 3: check and combine the answers
# ---------------------------------------------------------------------------

def _text(value):
    """The AI sometimes returns a list instead of a string: join it into text."""
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value or "").strip()


def clean_result(result):
    """Keep only well-formed parts of one AI answer."""
    cards = []
    for card in result.get("flashcards") or []:
        if isinstance(card, dict):
            question = _text(card.get("question"))
            answer = _text(card.get("answer"))
            if question and answer:  # skip half-empty cards
                cards.append({"question": question, "answer": answer})
    return {
        "key_concepts": _text(result.get("key_concepts")),
        "explanation": _text(result.get("explanation")),
        "examples": _text(result.get("examples")),
        "flashcards": cards,
    }


def combine_results(results):
    """Merge the answers from several batches into one summary + at most MAX_FLASHCARDS cards."""
    combined = {
        "key_concepts": "\n".join(r["key_concepts"] for r in results if r["key_concepts"]),
        "explanation": "\n\n".join(r["explanation"] for r in results if r["explanation"]),
        "examples": "\n\n".join(r["examples"] for r in results if r["examples"]),
        "flashcards": [card for r in results for card in r["flashcards"]][:MAX_FLASHCARDS],
    }
    if not combined["key_concepts"] and not combined["flashcards"]:
        raise GenerationError("The AI didn't return a summary or flashcards. Try Regenerate.")
    return combined


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def _set_error(lecture_id, message):
    """Save the error on the lecture (None = no error), so the pages can show it."""
    conn = get_connection()
    conn.execute("UPDATE lectures SET ai_error = ? WHERE id = ?", (message, lecture_id))
    conn.commit()
    conn.close()


def generate_for_lecture(lecture_id, language="en"):
    """
    Full pipeline for one lecture: images -> AI -> database.
    language: "en" or "fr" (the student's site language).
    Returns (ok, error_message). Never crashes the site: errors are saved on the lecture.
    """
    conn = get_connection()
    lecture = conn.execute("SELECT pdf_path FROM lectures WHERE id = ?", (lecture_id,)).fetchone()
    conn.close()
    if lecture is None:
        return False, "Lecture not found."

    language_name = "French" if language == "fr" else "English"

    try:
        # 1. PDF -> page images
        images = pdf_to_images(lecture["pdf_path"])

        # 2. One AI call per batch. Each batch asks for its share of the 10 cards,
        #    so a long lecture's cards cover all of it, not just the first pages.
        batches = batch_pages(images)
        cards_per_batch = math.ceil(MAX_FLASHCARDS / len(batches))
        results = [clean_result(ask_ai(batch, language_name, cards_per_batch)) for batch in batches]

        # 3. Combine and check
        final = combine_results(results)

    except GenerationError as error:
        _set_error(lecture_id, str(error))
        return False, str(error)
    except Exception as error:  # network problems, wrong key, missing package...
        message = f"Generation failed: {error}"
        _set_error(lecture_id, message)
        return False, message

    # 4. Save everything in one go. Old results are deleted first (for "Regenerate").
    conn = get_connection()
    conn.execute("DELETE FROM summaries WHERE lecture_id = ?", (lecture_id,))
    conn.execute("DELETE FROM flashcards WHERE lecture_id = ?", (lecture_id,))
    conn.execute(
        "INSERT INTO summaries (lecture_id, key_concepts, explanation, examples) VALUES (?, ?, ?, ?)",
        (lecture_id, final["key_concepts"], final["explanation"], final["examples"]),
    )
    conn.executemany(
        "INSERT INTO flashcards (lecture_id, question, answer) VALUES (?, ?, ?)",
        [(lecture_id, c["question"], c["answer"]) for c in final["flashcards"]],
    )
    conn.execute("UPDATE lectures SET ai_error = NULL WHERE id = ?", (lecture_id,))
    conn.commit()
    conn.close()
    return True, None


if __name__ == "__main__":
    # Quick test without the website: put a PDF at uploads/test.pdf and run:  python ai_generator.py
    pages = pdf_to_images(os.path.join("uploads", "test.pdf"))
    print(f"{len(pages)} pages converted")
    print(json.dumps(clean_result(ask_ai(pages[:3])), indent=2, ensure_ascii=False))
