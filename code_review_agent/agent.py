"""Code Review Agent — ADK agent definition."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent

from code_review_agent.tools import (
    calculate_complexity_metrics,
    check_security_patterns,
    detect_code_smells,
)

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

INSTRUCTION = """\
You are an expert Code Reviewer AI. You analyze code snippets for quality,
security vulnerabilities, and maintainability.

Rules:
- Always call at least one tool before providing feedback.
- Use `detect_code_smells` to find structural issues.
- Use `check_security_patterns` to find security vulnerabilities.
- Use `calculate_complexity_metrics` for Python to assess maintainability.
- Present findings grouped by severity: critical → high → medium → low.
- Provide specific, actionable recommendations for each finding.
- If no issues are found, confirm the code looks clean.
- Decline non-code questions in one sentence.
"""

root_agent = Agent(
    name="code_review_agent",
    model=os.environ.get("CODE_REVIEW_MODEL", "gemini-2.5-flash"),
    description=(
        "A code review agent that detects code smells, security vulnerabilities, "
        "and calculates complexity metrics for Python and other languages."
    ),
    instruction=INSTRUCTION,
    tools=[detect_code_smells, check_security_patterns, calculate_complexity_metrics],
)
