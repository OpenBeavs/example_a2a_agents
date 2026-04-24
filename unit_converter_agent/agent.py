"""
Unit Converter Agent
====================
A Google ADK agent that converts between units of length, temperature,
weight/mass, volume, speed, area, and data storage — all pure Python, no
external APIs needed.

No external API keys needed beyond GOOGLE_API_KEY for Gemini.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

# ─────────────────────────────────────────
# Unit tables (all convert → SI base, then SI base → target)
# ─────────────────────────────────────────

_LENGTH_TO_METERS: dict[str, float] = {
    "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
    "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
    "m": 1.0, "meter": 1.0, "meters": 1.0,
    "km": 1000.0, "kilometer": 1000.0, "kilometers": 1000.0,
    "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
    "ft": 0.3048, "foot": 0.3048, "feet": 0.3048,
    "yd": 0.9144, "yard": 0.9144, "yards": 0.9144,
    "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
    "nmi": 1852.0, "nautical mile": 1852.0, "nautical miles": 1852.0,
}

_WEIGHT_TO_KG: dict[str, float] = {
    "mg": 0.000001, "milligram": 0.000001, "milligrams": 0.000001,
    "g": 0.001, "gram": 0.001, "grams": 0.001,
    "kg": 1.0, "kilogram": 1.0, "kilograms": 1.0,
    "t": 1000.0, "tonne": 1000.0, "metric ton": 1000.0,
    "oz": 0.0283495, "ounce": 0.0283495, "ounces": 0.0283495,
    "lb": 0.453592, "pound": 0.453592, "pounds": 0.453592,
    "st": 6.35029, "stone": 6.35029, "stones": 6.35029,
    "ton": 907.185, "short ton": 907.185, "us ton": 907.185,
}

_VOLUME_TO_LITERS: dict[str, float] = {
    "ml": 0.001, "milliliter": 0.001, "milliliters": 0.001,
    "l": 1.0, "liter": 1.0, "liters": 1.0,
    "m3": 1000.0, "cubic meter": 1000.0,
    "tsp": 0.00492892, "teaspoon": 0.00492892, "teaspoons": 0.00492892,
    "tbsp": 0.0147868, "tablespoon": 0.0147868, "tablespoons": 0.0147868,
    "fl oz": 0.0295735, "fluid ounce": 0.0295735, "fluid ounces": 0.0295735,
    "cup": 0.236588, "cups": 0.236588,
    "pt": 0.473176, "pint": 0.473176, "pints": 0.473176,
    "qt": 0.946353, "quart": 0.946353, "quarts": 0.946353,
    "gal": 3.78541, "gallon": 3.78541, "gallons": 3.78541,
}

_SPEED_TO_MPS: dict[str, float] = {
    "m/s": 1.0, "mps": 1.0, "meters per second": 1.0,
    "km/h": 0.277778, "kph": 0.277778, "kilometers per hour": 0.277778,
    "mph": 0.44704, "miles per hour": 0.44704,
    "knot": 0.514444, "knots": 0.514444,
    "ft/s": 0.3048, "fps": 0.3048, "feet per second": 0.3048,
}

_DATA_TO_BYTES: dict[str, float] = {
    "b": 1, "byte": 1, "bytes": 1,
    "kb": 1024, "kilobyte": 1024, "kilobytes": 1024,
    "mb": 1024**2, "megabyte": 1024**2, "megabytes": 1024**2,
    "gb": 1024**3, "gigabyte": 1024**3, "gigabytes": 1024**3,
    "tb": 1024**4, "terabyte": 1024**4, "terabytes": 1024**4,
    "pb": 1024**5, "petabyte": 1024**5, "petabytes": 1024**5,
}


def _table_convert(value: float, from_unit: str, to_unit: str, table: dict[str, float]) -> dict:
    f_key = from_unit.lower().strip()
    t_key = to_unit.lower().strip()
    if f_key not in table:
        return {"status": "error", "error_message": f"Unknown unit '{from_unit}'. Valid: {', '.join(sorted(set(table)))}"}
    if t_key not in table:
        return {"status": "error", "error_message": f"Unknown unit '{to_unit}'. Valid: {', '.join(sorted(set(table)))}"}
    base = value * table[f_key]
    result = base / table[t_key]
    return {"status": "success", "input": value, "from_unit": from_unit, "to_unit": to_unit, "result": round(result, 8)}


# ─────────────────────────────────────────
# Tools
# ─────────────────────────────────────────

def convert_length(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a length value between units.

    Supported units: mm, cm, m, km, in, ft, yd, mi, nmi (and spelled-out names).

    Args:
        value: Numeric value to convert.
        from_unit: Source unit (e.g. "ft", "miles", "cm").
        to_unit: Target unit (e.g. "m", "km", "inches").

    Returns:
        dict with 'status', 'result', and unit labels, or 'error_message'.
    """
    return _table_convert(value, from_unit, to_unit, _LENGTH_TO_METERS)


def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a temperature value between Celsius, Fahrenheit, and Kelvin.

    Args:
        value: Numeric temperature to convert.
        from_unit: Source scale ("celsius"/"c", "fahrenheit"/"f", "kelvin"/"k").
        to_unit: Target scale.

    Returns:
        dict with 'status' and 'result', or 'error_message'.
    """
    aliases = {
        "c": "celsius", "celsius": "celsius",
        "f": "fahrenheit", "fahrenheit": "fahrenheit",
        "k": "kelvin", "kelvin": "kelvin",
    }
    src = aliases.get(from_unit.lower().strip())
    dst = aliases.get(to_unit.lower().strip())
    if not src:
        return {"status": "error", "error_message": f"Unknown temperature unit '{from_unit}'. Use c/f/k."}
    if not dst:
        return {"status": "error", "error_message": f"Unknown temperature unit '{to_unit}'. Use c/f/k."}

    if src == dst:
        return {"status": "success", "input": value, "from_unit": from_unit, "to_unit": to_unit, "result": value}

    to_celsius: dict[str, float] = {}
    if src == "celsius":
        celsius = value
    elif src == "fahrenheit":
        celsius = (value - 32) * 5 / 9
    else:
        celsius = value - 273.15

    if dst == "celsius":
        result = celsius
    elif dst == "fahrenheit":
        result = celsius * 9 / 5 + 32
    else:
        result = celsius + 273.15

    return {"status": "success", "input": value, "from_unit": from_unit, "to_unit": to_unit, "result": round(result, 4)}


def convert_weight(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a weight/mass value between units.

    Supported: mg, g, kg, t, oz, lb, st, ton (and spelled-out names).

    Args:
        value: Numeric mass to convert.
        from_unit: Source unit.
        to_unit: Target unit.

    Returns:
        dict with 'status' and 'result', or 'error_message'.
    """
    return _table_convert(value, from_unit, to_unit, _WEIGHT_TO_KG)


def convert_volume(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a volume value between units.

    Supported: ml, l, m3, tsp, tbsp, fl oz, cup, pt, qt, gal (and spelled-out names).

    Args:
        value: Numeric volume to convert.
        from_unit: Source unit.
        to_unit: Target unit.

    Returns:
        dict with 'status' and 'result', or 'error_message'.
    """
    return _table_convert(value, from_unit, to_unit, _VOLUME_TO_LITERS)


def convert_speed(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a speed value between units.

    Supported: m/s, km/h, mph, knots, ft/s (and spelled-out names).

    Args:
        value: Numeric speed to convert.
        from_unit: Source unit.
        to_unit: Target unit.

    Returns:
        dict with 'status' and 'result', or 'error_message'.
    """
    return _table_convert(value, from_unit, to_unit, _SPEED_TO_MPS)


def convert_data_storage(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert data storage between bytes, KB, MB, GB, TB, PB.

    Args:
        value: Numeric data size to convert.
        from_unit: Source unit (e.g. "MB", "gigabytes").
        to_unit: Target unit.

    Returns:
        dict with 'status' and 'result', or 'error_message'.
    """
    return _table_convert(value, from_unit, to_unit, _DATA_TO_BYTES)


# ─────────────────────────────────────────
# Agent Definition
# ─────────────────────────────────────────

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
        "speed, and data storage — all conversions computed locally with no external APIs."
    ),
    instruction=INSTRUCTION,
    tools=[convert_length, convert_temperature, convert_weight, convert_volume, convert_speed, convert_data_storage],
)
