"""Trivia Agent — tool functions (no ADK dependency)."""

from __future__ import annotations

import html
import json
import random
import urllib.parse
import urllib.request

_OPENTDB_BASE = "https://opentdb.com"


def _http_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "TriviaAgent/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def list_trivia_categories() -> dict:
    """Return all available trivia categories from Open Trivia DB.

    Returns:
        dict with 'status' and 'categories' list (id + name), or 'error_message'.
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
        category_id: Category ID (0 = any category).
        difficulty: "easy", "medium", or "hard".
        question_type: "multiple" or "boolean".

    Returns:
        dict with 'status' and 'question' (text, category, difficulty, choices,
        correct_answer), or 'error_message'.
    """
    difficulty = difficulty.lower()
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"

    params: dict = {"amount": 1, "type": question_type, "difficulty": difficulty}
    if category_id > 0:
        params["category"] = category_id

    url = f"{_OPENTDB_BASE}/api.php?{urllib.parse.urlencode(params)}"

    try:
        data = _http_get(url)
    except Exception as exc:
        return {"status": "error", "error_message": f"Trivia API request failed: {exc}"}

    response_code = data.get("response_code", -1)
    if response_code != 0:
        messages = {
            1: "No results for these parameters.",
            2: "Invalid parameters.",
            5: "Rate limited — try again.",
        }
        return {"status": "error", "error_message": messages.get(response_code, f"API error code {response_code}.")}

    results = data.get("results", [])
    if not results:
        return {"status": "error", "error_message": "Empty results from API."}

    r = results[0]
    correct = html.unescape(r["correct_answer"])
    incorrect = [html.unescape(a) for a in r.get("incorrect_answers", [])]
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
        dict with 'status', 'is_correct', and 'feedback'.
    """
    if not user_answer.strip() or not correct_answer.strip():
        return {"status": "error", "error_message": "Both user_answer and correct_answer are required."}

    is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
    return {
        "status": "success",
        "is_correct": is_correct,
        "feedback": "Correct! Well done." if is_correct else f"Incorrect. The correct answer was: {correct_answer}",
    }
