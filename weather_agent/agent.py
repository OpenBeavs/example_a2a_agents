"""
Weather Agent
=============
A Google ADK agent that retrieves current weather and forecasts for any city
using the Open-Meteo API (free, no API key required).

No external API keys needed beyond GOOGLE_API_KEY for Gemini.
"""

from __future__ import annotations

import os
import urllib.request
import urllib.parse
import json
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

_WMO_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ heavy hail",
}


def _http_get(url: str) -> dict:
    """Fetch JSON from url via stdlib urllib (no requests dependency)."""
    req = urllib.request.Request(url, headers={"User-Agent": "WeatherAgent/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


# ─────────────────────────────────────────
# Tools
# ─────────────────────────────────────────

def geocode_city(city_name: str) -> dict:
    """Resolve a city name to latitude/longitude coordinates.

    Uses the Open-Meteo geocoding API (no auth required).

    Args:
        city_name: Name of the city (e.g. "Portland", "Tokyo", "London, UK").

    Returns:
        dict with 'status' and 'location' (name, country, lat, lon, timezone)
        or 'error_message'.
    """
    if not city_name.strip():
        return {"status": "error", "error_message": "city_name cannot be empty."}

    encoded = urllib.parse.quote(city_name.strip())
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=en&format=json"

    try:
        data = _http_get(url)
    except Exception as exc:
        return {"status": "error", "error_message": f"Geocoding request failed: {exc}"}

    results = data.get("results", [])
    if not results:
        return {"status": "not_found", "error_message": f"No location found for '{city_name}'."}

    r = results[0]
    return {
        "status": "success",
        "location": {
            "name": r.get("name", city_name),
            "country": r.get("country", ""),
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "timezone": r.get("timezone", "UTC"),
        },
    }


def get_current_weather(latitude: float, longitude: float) -> dict:
    """Fetch current weather conditions for given coordinates.

    Uses Open-Meteo (no auth required).

    Args:
        latitude: Decimal latitude of the location.
        longitude: Decimal longitude of the location.

    Returns:
        dict with 'status' and 'current' weather data or 'error_message'.
    """
    params = urllib.parse.urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
        "wind_speed_unit": "mph",
        "temperature_unit": "fahrenheit",
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"

    try:
        data = _http_get(url)
    except Exception as exc:
        return {"status": "error", "error_message": f"Weather request failed: {exc}"}

    cur = data.get("current", {})
    code = cur.get("weather_code", -1)
    return {
        "status": "success",
        "current": {
            "temperature_f": cur.get("temperature_2m"),
            "feels_like_f": cur.get("apparent_temperature"),
            "humidity_pct": cur.get("relative_humidity_2m"),
            "wind_speed_mph": cur.get("wind_speed_10m"),
            "precipitation_in": cur.get("precipitation"),
            "condition": _WMO_CODES.get(code, f"Unknown (code {code})"),
        },
    }


def get_forecast(latitude: float, longitude: float, days: int = 5) -> dict:
    """Fetch a multi-day daily weather forecast for given coordinates.

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        days: Number of forecast days (1–16). Defaults to 5.

    Returns:
        dict with 'status' and 'forecast' list (one entry per day) or 'error_message'.
    """
    days = max(1, min(days, 16))
    params = urllib.parse.urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "forecast_days": days,
        "wind_speed_unit": "mph",
        "temperature_unit": "fahrenheit",
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"

    try:
        data = _http_get(url)
    except Exception as exc:
        return {"status": "error", "error_message": f"Forecast request failed: {exc}"}

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    wind = daily.get("wind_speed_10m_max", [])

    forecast = [
        {
            "date": dates[i],
            "condition": _WMO_CODES.get(codes[i], f"Code {codes[i]}"),
            "high_f": highs[i],
            "low_f": lows[i],
            "precipitation_in": precip[i],
            "max_wind_mph": wind[i],
        }
        for i in range(len(dates))
    ]

    return {"status": "success", "forecast": forecast}


# ─────────────────────────────────────────
# Agent Definition
# ─────────────────────────────────────────

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
