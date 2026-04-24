"""
Trivia Agent
============
A Google ADK agent that fetches trivia questions from the Open Trivia Database
(opentdb.com — free, no API key) and evaluates answers.

No external API keys needed beyond GOOGLE_API_KEY for Gemini.
"""

from __future__ import annotations

import os
import html
import urllib.request
import urllib.parse
import json
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

_OPENTDB_BASE = "https://opentdb.com"


def _http_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "TriviaAgent/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


# ─────────────────────────────────────────
# Tools
# ─────────────────────────────────────────

def list_trivia_categories() -> dict:
    """Return all available trivia categories from Open Trivia DB.

    Returns:
        dict with 'status' and 'categories' list (each with id and name),
        or 'error_message'.
    """
    try:
        data = _http_get(f"{_OPENTDB_BASE}/api_category.php")
    except Exception as exc:
        return {"status": "error", "error_message": f"Could not fetch categories: {exc}"}

    categories = [
        {"id": c["id"], "name": c["name"]}
        for c in data.get("trivia_categories", [])
    ]
    return {"status": "success", "categories": categories}


def fetch_trivia_question(
    category_id: int = 0,
    difficulty: str = "medium",
    question_type: str = "multiple",
) -> dict:
    """Fetch a single trivia question from Open Trivia DB.

    Args:
        category_id: Category ID from `list_trivia_categories`. 0 = any category.
        difficulty: One of "easy", "medium", "hard". Defaults to "medium".
        question_type: "multiple" (4 choices) or "boolean" (True/False).

    Returns:
        dict with 'status' and 'question' (text, category, difficulty, choices,
        correct_answer) or 'error_message'.
    """
    difficulty = difficulty.lower()
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"

    params: dict[str, str | int] = {
        "amount": 1,
        "type": question_type,
        "difficulty": difficulty,
    }
    if category_id > 0:
        params["category"] = category_id

    url = f"{_OPENTDB_BASE}/api.php?{urllib.parse.urlencode(params)}"

    try:
        data = _http_get(url)
    except Exception as exc:
        return {"status": "error", "error_message": f"Trivia API request failed: {exc}"}

    response_code = data.get("response_code", -1)
    if response_code != 0:
        messages = {1: "No results for these parameters.", 2: "Invalid parameters.", 5: "Rate limited — try again."}
        return {"status": "error", "error_message": messages.get(response_code, f"API error code {response_code}.")}

    results = data.get("results", [])
    if not results:
        return {"status": "error", "error_message": "Empty results from API."}

    r = results[0]
    correct = html.unescape(r["correct_answer"])
    incorrect = [html.unescape(a) for a in r.get("incorrect_answers", [])]

    import random
    choices = incorrect + [correct]
    random.shuffle(choices)

    return {
        "status": "success",
        "question": {
            "text": html.unescape(r["question"]),
            "category": html.unescape(r["category"]),
            "difficulty": r["difficulty"],
            "type": r["type"],
            "choices": choices,
            "correct_answer": correct,
        },
    }


def evaluate_answer(user_answer: str, correct_answer: str) -> dict:
    """Check whether a user's answer matches the correct answer (case-insensitive).

    Args:
        user_answer: The answer provided by the user.
        correct_answer: The correct answer string.

    Returns:
        dict with 'status', 'is_correct' boolean, and 'feedback' message.
    """
    if not user_answer.strip() or not correct_answer.strip():
        return {"status": "error", "error_message": "Both user_answer and correct_answer are required."}

    is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
    return {
        "status": "success",
        "is_correct": is_correct,
        "feedback": "Correct! Well done." if is_correct else f"Incorrect. The correct answer was: {correct_answer}",
    }


# ─────────────────────────────────────────
# Agent Definition
# ─────────────────────────────────────────

INSTRUCTION = """\
You are an enthusiastic Trivia Host AI. You quiz users with fun trivia questions
from a wide range of categories.

Rules:
- Call `list_trivia_categories` when the user asks about available categories.
- Call `fetch_trivia_question` to get a new question — present the choices clearly.
- Call `evaluate_answer` to check the user's answer after they respond.
- Keep track of score within the conversation (correct answers / total asked).
- Present questions in a fun, engaging way. Give a brief fact after each answer.
- If the API is unavailable, apologize and offer a fun fact instead.
"""

root_agent = Agent(
    name="trivia_agent",
    model=os.environ.get("TRIVIA_AGENT_MODEL", "gemini-2.5-flash"),
    description=(
        "A trivia host agent that fetches questions from Open Trivia DB across "
        "dozens of categories and difficulties, then evaluates user answers."
    ),
    instruction=INSTRUCTION,
    tools=[list_trivia_categories, fetch_trivia_question, evaluate_answer],
)
