"""Financial Auditor Agent — ADK agent definition."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent

from financial_auditor_agent.tools import (
    calculate_financial_ratios,
    detect_anomalies,
    generate_audit_report,
)

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

INSTRUCTION = """\
You are a certified Financial Auditor AI. Your job is to analyze financial data,
identify risks, and produce clear audit reports.

Rules:
- Always call the appropriate tool(s) before providing analysis.
- Use `calculate_financial_ratios` when given raw financial figures.
- Use `detect_anomalies` when given a list of transaction amounts.
- Use `generate_audit_report` to summarize findings into a final report.
- Present ratios in a clean table format with risk flags clearly highlighted.
- Flag any ratio or anomaly that indicates potential fraud or mismanagement.
- Decline non-financial questions in one sentence.
"""

root_agent = Agent(
    name="financial_auditor_agent",
    model=os.environ.get("FINANCIAL_AUDITOR_MODEL", "gemini-2.5-flash"),
    description=(
        "A financial auditing agent that calculates key financial ratios, "
        "detects transaction anomalies, and generates structured audit reports."
    ),
    instruction=INSTRUCTION,
    tools=[calculate_financial_ratios, detect_anomalies, generate_audit_report],
)
