"""Trivia Agent — ADK agent definition."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent

from trivia_agent.tools import evaluate_answer, fetch_trivia_question, list_trivia_categories

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

INSTRUCTION = """\
You are an enthusiastic Trivia Host AI. You quiz users with fun trivia questions
from a wide range of categories.

Rules:
- Call `list_trivia_categories` when the user asks about available categories.
- Call `fetch_trivia_question` to get a new question — present the choices clearly.
- Call `evaluate_answer` to check the user's answer after they respond.
- Keep track of score within the conversation (correct / total asked).
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
