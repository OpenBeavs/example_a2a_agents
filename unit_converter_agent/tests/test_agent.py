"""Tests for unit_converter_agent tools."""

import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from unit_converter_agent.tools import (
    convert_length,
    convert_temperature,
    convert_weight,
    convert_volume,
    convert_speed,
    convert_data_storage,
)


class TestConvertLength:
    def test_feet_to_meters(self):
        result = convert_length(1.0, "ft", "m")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 0.3048, rel_tol=1e-5)

    def test_miles_to_kilometers(self):
        result = convert_length(1.0, "miles", "km")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 1.609344, rel_tol=1e-5)

    def test_same_unit_is_identity(self):
        result = convert_length(42.0, "m", "m")
        assert result["status"] == "success"
        assert result["result"] == 42.0

    def test_inches_to_centimeters(self):
        result = convert_length(1.0, "in", "cm")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 2.54, rel_tol=1e-5)

    def test_unknown_from_unit_returns_error(self):
        result = convert_length(10.0, "lightyears", "m")
        assert result["status"] == "error"

    def test_unknown_to_unit_returns_error(self):
        result = convert_length(10.0, "m", "cubits")
        assert result["status"] == "error"

    def test_case_insensitive(self):
        result = convert_length(1.0, "KM", "M")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 1000.0, rel_tol=1e-5)


class TestConvertTemperature:
    def test_celsius_to_fahrenheit(self):
        result = convert_temperature(100.0, "c", "f")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 212.0, rel_tol=1e-5)

    def test_fahrenheit_to_celsius(self):
        result = convert_temperature(32.0, "f", "c")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 0.0, abs_tol=1e-5)

    def test_celsius_to_kelvin(self):
        result = convert_temperature(0.0, "celsius", "kelvin")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 273.15, rel_tol=1e-5)

    def test_kelvin_to_celsius(self):
        result = convert_temperature(273.15, "k", "c")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 0.0, abs_tol=1e-4)

    def test_body_temperature_f_to_c(self):
        result = convert_temperature(98.6, "f", "c")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 37.0, abs_tol=0.01)

    def test_same_unit_identity(self):
        result = convert_temperature(25.0, "c", "celsius")
        assert result["status"] == "success"
        assert result["result"] == 25.0

    def test_unknown_unit_returns_error(self):
        result = convert_temperature(100.0, "rankine", "c")
        assert result["status"] == "error"


class TestConvertWeight:
    def test_pounds_to_kilograms(self):
        result = convert_weight(1.0, "lb", "kg")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 0.453592, rel_tol=1e-4)

    def test_kilograms_to_grams(self):
        result = convert_weight(1.0, "kg", "g")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 1000.0, rel_tol=1e-5)

    def test_ounces_to_grams(self):
        result = convert_weight(1.0, "oz", "g")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 28.3495, rel_tol=1e-3)

    def test_unknown_unit_returns_error(self):
        result = convert_weight(10.0, "slugs", "kg")
        assert result["status"] == "error"


class TestConvertVolume:
    def test_gallons_to_liters(self):
        result = convert_volume(1.0, "gal", "l")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 3.78541, rel_tol=1e-4)

    def test_cups_to_ml(self):
        result = convert_volume(1.0, "cup", "ml")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 236.588, rel_tol=1e-3)

    def test_unknown_unit_returns_error(self):
        result = convert_volume(1.0, "barrels", "l")
        assert result["status"] == "error"


class TestConvertSpeed:
    def test_mph_to_kph(self):
        result = convert_speed(60.0, "mph", "km/h")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 96.5606, rel_tol=1e-3)

    def test_knots_to_mph(self):
        result = convert_speed(1.0, "knots", "mph")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 1.15078, rel_tol=1e-3)

    def test_unknown_unit_returns_error(self):
        result = convert_speed(100.0, "warp", "mph")
        assert result["status"] == "error"


class TestConvertDataStorage:
    def test_gb_to_mb(self):
        result = convert_data_storage(1.0, "gb", "mb")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 1024.0, rel_tol=1e-5)

    def test_tb_to_gb(self):
        result = convert_data_storage(1.0, "tb", "gb")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 1024.0, rel_tol=1e-5)

    def test_bytes_to_kilobytes(self):
        result = convert_data_storage(1024.0, "bytes", "kb")
        assert result["status"] == "success"
        assert math.isclose(result["result"], 1.0, rel_tol=1e-5)

    def test_unknown_unit_returns_error(self):
        result = convert_data_storage(1.0, "floppy", "mb")
        assert result["status"] == "error"
