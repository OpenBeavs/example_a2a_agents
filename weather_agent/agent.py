"""Weather Agent — ADK agent definition."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent

from weather_agent.tools import geocode_city, get_current_weather, get_forecast

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

INSTRUCTION = """\
You are a friendly and accurate Weather Agent. You provide current conditions
and forecasts for any city in the world.

Rules:
- Always call `geocode_city` first to get coordinates, then call the weather tool.
- For current conditions, call `get_current_weather`.
- For forecasts, call `get_forecast` with the appropriate number of days.
- Present temperatures in Fahrenheit and wind in MPH.
- If a city cannot be found, suggest the user try a nearby major city.
- Decline non-weather questions in one sentence.
"""

root_agent = Agent(
    name="weather_agent",
    model=os.environ.get("WEATHER_AGENT_MODEL", "gemini-2.5-flash"),
    description=(
        "A weather agent that provides real-time current conditions and "
        "multi-day forecasts for any city using the Open-Meteo API."
    ),
    instruction=INSTRUCTION,
    tools=[geocode_city, get_current_weather, get_forecast],
)
