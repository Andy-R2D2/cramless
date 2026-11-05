"""
ai_generator.py — ROLE 2. Lecture PDF -> summary + up to 10 flashcards.

This is the ONLY place we use AI. Results are saved in the database once,
so we don't pay for the same lecture twice.

Steps:
  1. PDF pages -> images (PyMuPDF), so math formulas are read correctly
  2. Send the images to the OpenAI API, ask for JSON
  3. Save the summary and flashcards in the database

Put your key in a .env file:  OPENAI_API_KEY=sk-...
"""

import base64
import json
import os

import fitz  # PyMuPDF
from dotenv import load_dotenv

from database import get_connection

load_dotenv()  # reads OPENAI_API_KEY from the .env file

MAX_FLASHCARDS = 10
PAGES_PER_CALL = 12  # long lectures are sent in batches

PROMPT = """Using ONLY these lecture slides, return JSON with these keys:
"key_concepts" (short list as text), "explanation" (in-depth, as text),
"examples" (one real-life example per concept, as text),
"flashcards" (list of up to 10 objects with "question" and "answer").
Write formulas in LaTeX: $...$ inline, $$...$$ on their own line.
Respond in {language}."""


def pdf_to_images(pdf_path, dpi=150):
    """Turn each PDF page into a PNG image (bytes). 150 dpi is usually enough."""
    images = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            images.append(page.get_pixmap(dpi=dpi).tobytes("png"))
    return images


def ask_ai(images, language="English"):
    """
    Send page images to OpenAI and return the answer as a Python dict.

    TODO (Role 2):
      - test with a real lecture and check the JSON comes back correctly
      - try a calculus lecture: are the formulas right?
    """
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Build the message: the prompt text + every page as an image
    content = [{"type": "text", "text": PROMPT.format(language=language)}]
    for png in images:
        b64 = base64.b64encode(png).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},  # forces valid JSON
        messages=[{"role": "user", "content": content}],
    )
    return json.loads(response.choices[0].message.content)


def generate_for_lecture(lecture_id, language="English"):
    """
    Full pipeline for one lecture: images -> AI -> database.

    TODO (Role 2):
      1. get the lecture's pdf_path from the database
      2. images = pdf_to_images(pdf_path)
      3. split images into batches of PAGES_PER_CALL and call ask_ai() for each
      4. combine the results, keep at most MAX_FLASHCARDS cards
      5. delete any old summary/flashcards for this lecture (for "regenerate")
      6. INSERT the summary into `summaries` and the cards into `flashcards`
      7. wrap it in try/except so one bad lecture doesn't crash the site
    """
    pass


if __name__ == "__main__":
    # Quick test without the website: put a PDF in uploads/ and run this file
    pages = pdf_to_images("uploads/test.pdf")
    print(f"{len(pages)} pages converted")
    # print(ask_ai(pages[:3]))  # uncomment once your API key is in .env
