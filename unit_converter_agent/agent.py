"""Unit Converter Agent — ADK agent definition."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent

from unit_converter_agent.tools import (
    convert_data_storage,
    convert_length,
    convert_speed,
    convert_temperature,
    convert_volume,
    convert_weight,
)

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

INSTRUCTION = """\
You are a precise Unit Converter AI. You convert any quantity between supported
units of measurement accurately and instantly.

Rules:
- Always call the appropriate conversion tool.
- Support: length, temperature, weight, volume, speed, data storage.
- Present results clearly: "X <from_unit> = Y <to_unit>".
- If the unit is ambiguous (e.g. "ton"), ask for clarification.
- For chained conversions (e.g. miles to cm), chain two tool calls.
- Decline non-conversion questions in one sentence.
"""

root_agent = Agent(
    name="unit_converter_agent",
    model=os.environ.get("UNIT_CONVERTER_MODEL", "gemini-2.5-flash"),
    description=(
        "A unit conversion agent supporting length, temperature, weight, volume, "
        "speed, and data storage — all computed locally with no external APIs."
    ),
    instruction=INSTRUCTION,
    tools=[convert_length, convert_temperature, convert_weight, convert_volume, convert_speed, convert_data_storage],
)
