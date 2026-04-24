"""Tests for weather_agent tools.

HTTP calls are mocked so tests run fully offline.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from weather_agent.tools import geocode_city, get_current_weather, get_forecast


def _mock_urlopen(response_data: dict):
    """Return a context-manager mock that yields a readable mock response."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_resp)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx


GEOCODE_RESPONSE = {
    "results": [
        {
            "name": "Portland",
            "country": "United States",
            "latitude": 45.5231,
            "longitude": -122.6765,
            "timezone": "America/Los_Angeles",
        }
    ]
}

CURRENT_WEATHER_RESPONSE = {
    "current": {
        "temperature_2m": 62.5,
        "apparent_temperature": 59.0,
        "relative_humidity_2m": 72,
        "weather_code": 3,
        "wind_speed_10m": 12.4,
        "precipitation": 0.0,
    }
}

FORECAST_RESPONSE = {
    "daily": {
        "time": ["2024-04-01", "2024-04-02", "2024-04-03"],
        "weather_code": [1, 63, 0],
        "temperature_2m_max": [68.0, 55.0, 72.0],
        "temperature_2m_min": [48.0, 45.0, 52.0],
        "precipitation_sum": [0.0, 0.45, 0.0],
        "wind_speed_10m_max": [10.0, 18.0, 8.0],
    }
}


class TestGeocodeCity:
    @patch("urllib.request.urlopen")
    def test_success(self, mock_open):
        mock_open.return_value = _mock_urlopen(GEOCODE_RESPONSE)
        result = geocode_city("Portland")
        assert result["status"] == "success"
        loc = result["location"]
        assert loc["name"] == "Portland"
        assert loc["latitude"] == 45.5231
        assert loc["country"] == "United States"

    @patch("urllib.request.urlopen")
    def test_not_found(self, mock_open):
        mock_open.return_value = _mock_urlopen({"results": []})
        result = geocode_city("ZZZNotACity")
        assert result["status"] == "not_found"

    def test_empty_city_returns_error(self):
        result = geocode_city("   ")
        assert result["status"] == "error"

    @patch("urllib.request.urlopen", side_effect=Exception("timeout"))
    def test_network_error_returns_error(self, mock_open):
        result = geocode_city("London")
        assert result["status"] == "error"
        assert "timeout" in result["error_message"]


class TestGetCurrentWeather:
    @patch("urllib.request.urlopen")
    def test_success(self, mock_open):
        mock_open.return_value = _mock_urlopen(CURRENT_WEATHER_RESPONSE)
        result = get_current_weather(45.5231, -122.6765)
        assert result["status"] == "success"
        cur = result["current"]
        assert cur["temperature_f"] == 62.5
        assert cur["humidity_pct"] == 72
        assert cur["condition"] == "Overcast"  # code 3

    @patch("urllib.request.urlopen", side_effect=Exception("network error"))
    def test_network_error(self, mock_open):
        result = get_current_weather(0.0, 0.0)
        assert result["status"] == "error"

    @patch("urllib.request.urlopen")
    def test_unknown_weather_code_handled(self, mock_open):
        data = {**CURRENT_WEATHER_RESPONSE}
        data["current"] = {**data["current"], "weather_code": 999}
        mock_open.return_value = _mock_urlopen(data)
        result = get_current_weather(45.0, -120.0)
        assert result["status"] == "success"
        assert "999" in result["current"]["condition"]


class TestGetForecast:
    @patch("urllib.request.urlopen")
    def test_success(self, mock_open):
        mock_open.return_value = _mock_urlopen(FORECAST_RESPONSE)
        result = get_forecast(45.5231, -122.6765, days=3)
        assert result["status"] == "success"
        assert len(result["forecast"]) == 3

    @patch("urllib.request.urlopen")
    def test_forecast_fields(self, mock_open):
        mock_open.return_value = _mock_urlopen(FORECAST_RESPONSE)
        result = get_forecast(45.0, -120.0, days=3)
        day = result["forecast"][0]
        assert "date" in day
        assert "high_f" in day
        assert "low_f" in day
        assert "condition" in day
        assert "precipitation_in" in day

    @patch("urllib.request.urlopen")
    def test_days_clamped_to_16(self, mock_open):
        mock_open.return_value = _mock_urlopen(FORECAST_RESPONSE)
        # Should not raise; days clamped internally
        result = get_forecast(45.0, -120.0, days=99)
        assert result["status"] == "success"

    @patch("urllib.request.urlopen", side_effect=Exception("network error"))
    def test_network_error(self, mock_open):
        result = get_forecast(0.0, 0.0)
        assert result["status"] == "error"
