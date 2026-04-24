"""Tests for trivia_agent tools.

HTTP calls are mocked so tests run fully offline.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from trivia_agent.tools import list_trivia_categories, fetch_trivia_question, evaluate_answer


def _mock_urlopen(response_data: dict):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_resp)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx


CATEGORIES_RESPONSE = {
    "trivia_categories": [
        {"id": 9, "name": "General Knowledge"},
        {"id": 17, "name": "Science & Nature"},
        {"id": 23, "name": "History"},
    ]
}

QUESTION_RESPONSE = {
    "response_code": 0,
    "results": [
        {
            "category": "Science &amp; Nature",
            "type": "multiple",
            "difficulty": "medium",
            "question": "What is the chemical symbol for gold?",
            "correct_answer": "Au",
            "incorrect_answers": ["Ag", "Fe", "Cu"],
        }
    ],
}


class TestListTriviaCategories:
    @patch("urllib.request.urlopen")
    def test_returns_categories(self, mock_open):
        mock_open.return_value = _mock_urlopen(CATEGORIES_RESPONSE)
        result = list_trivia_categories()
        assert result["status"] == "success"
        assert len(result["categories"]) == 3

    @patch("urllib.request.urlopen")
    def test_category_structure(self, mock_open):
        mock_open.return_value = _mock_urlopen(CATEGORIES_RESPONSE)
        result = list_trivia_categories()
        cat = result["categories"][0]
        assert "id" in cat
        assert "name" in cat
        assert cat["id"] == 9

    @patch("urllib.request.urlopen", side_effect=Exception("network error"))
    def test_network_error_returns_error(self, mock_open):
        result = list_trivia_categories()
        assert result["status"] == "error"


class TestFetchTriviaQuestion:
    @patch("urllib.request.urlopen")
    def test_success(self, mock_open):
        mock_open.return_value = _mock_urlopen(QUESTION_RESPONSE)
        result = fetch_trivia_question()
        assert result["status"] == "success"
        q = result["question"]
        assert q["text"] == "What is the chemical symbol for gold?"
        assert q["correct_answer"] == "Au"

    @patch("urllib.request.urlopen")
    def test_html_entities_decoded(self, mock_open):
        mock_open.return_value = _mock_urlopen(QUESTION_RESPONSE)
        result = fetch_trivia_question()
        assert result["status"] == "success"
        assert result["question"]["category"] == "Science & Nature"

    @patch("urllib.request.urlopen")
    def test_choices_shuffled_contain_correct(self, mock_open):
        mock_open.return_value = _mock_urlopen(QUESTION_RESPONSE)
        result = fetch_trivia_question()
        assert "Au" in result["question"]["choices"]
        assert len(result["question"]["choices"]) == 4

    @patch("urllib.request.urlopen")
    def test_api_error_code_returns_error(self, mock_open):
        mock_open.return_value = _mock_urlopen({"response_code": 1, "results": []})
        result = fetch_trivia_question(category_id=9999)
        assert result["status"] == "error"

    @patch("urllib.request.urlopen")
    def test_invalid_difficulty_falls_back_to_medium(self, mock_open):
        mock_open.return_value = _mock_urlopen(QUESTION_RESPONSE)
        result = fetch_trivia_question(difficulty="impossible")
        assert result["status"] == "success"

    @patch("urllib.request.urlopen", side_effect=Exception("timeout"))
    def test_network_error(self, mock_open):
        result = fetch_trivia_question()
        assert result["status"] == "error"
        assert "timeout" in result["error_message"]


class TestEvaluateAnswer:
    def test_correct_answer(self):
        result = evaluate_answer("Au", "Au")
        assert result["status"] == "success"
        assert result["is_correct"] is True

    def test_case_insensitive_match(self):
        result = evaluate_answer("true", "True")
        assert result["is_correct"] is True

    def test_wrong_answer(self):
        result = evaluate_answer("Ag", "Au")
        assert result["status"] == "success"
        assert result["is_correct"] is False
        assert "Au" in result["feedback"]

    def test_whitespace_trimmed(self):
        result = evaluate_answer("  Paris  ", "Paris")
        assert result["is_correct"] is True

    def test_empty_user_answer_returns_error(self):
        result = evaluate_answer("", "Paris")
        assert result["status"] == "error"

    def test_empty_correct_answer_returns_error(self):
        result = evaluate_answer("Paris", "  ")
        assert result["status"] == "error"

    def test_feedback_contains_correct_answer_on_wrong(self):
        result = evaluate_answer("Berlin", "Paris")
        assert "Paris" in result["feedback"]
