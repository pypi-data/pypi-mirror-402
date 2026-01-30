"""Unit tests for WeatherPlugin."""

from unittest.mock import Mock, patch

import pytest
from aprsd.packets import core

from aprsd_openweathermap_plugin.weather import WeatherPlugin


class TestWeatherPlugin:
    """Test cases for WeatherPlugin."""

    @pytest.fixture
    def plugin(self):
        """Create a WeatherPlugin instance."""
        return WeatherPlugin()

    @pytest.fixture
    def mock_packet(self):
        """Create a mock packet."""
        packet = Mock(spec=core.Packet)
        packet.get = Mock(
            side_effect=lambda key, default=None: {
                "from_call": "TESTCALL",
                "message_text": "weather",
            }.get(key, default)
        )
        return packet

    @pytest.fixture
    def mock_aprs_fi_data(self):
        """Mock aprs.fi API response."""
        return {
            "entries": [
                {
                    "lat": 37.7749,
                    "lng": -122.4194,
                }
            ]
        }

    @pytest.fixture
    def mock_owm_data_metric(self):
        """Mock OpenWeatherMap API response with metric units."""
        return {
            "current": {
                "weather": [{"description": "clear sky"}],
                "temp": 20.5,
                "dew_point": 15.2,
                "wind_speed": 10.0,
                "wind_deg": 180,
                "humidity": 65,
            }
        }

    @pytest.fixture
    def mock_owm_data_imperial(self):
        """Mock OpenWeatherMap API response with imperial units."""
        return {
            "current": {
                "weather": [{"description": "clear sky"}],
                "temp": 68.9,
                "dew_point": 59.4,
                "wind_speed": 22.4,
                "wind_deg": 180,
                "humidity": 65,
            }
        }

    @pytest.fixture
    def mock_owm_data_with_gust(self):
        """Mock OpenWeatherMap API response with wind gust."""
        return {
            "current": {
                "weather": [{"description": "partly cloudy"}],
                "temp": 22.0,
                "dew_point": 18.0,
                "wind_speed": 15.0,
                "wind_deg": 270,
                "wind_gust": 25.0,
                "humidity": 70,
            }
        }

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.weather.own_util.fetch_openweathermap")
    def test_process_success_metric_units(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data_metric,
    ):
        """Test successful weather fetch with metric units."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_conf.units = "metric"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data_metric

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert "clear sky" in result
        assert "20.5C" in result
        assert "15.2C" in result
        assert "65%" in result
        assert "Wind" in result
        mock_get_aprs_fi.assert_called_once_with("test_aprs_fi_key", "TESTCALL")
        mock_fetch_owm.assert_called_once_with(
            37.7749, -122.4194, units="metric", exclude="minutely,hourly"
        )

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.weather.own_util.fetch_openweathermap")
    def test_process_success_imperial_units(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data_imperial,
    ):
        """Test successful weather fetch with imperial units."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_conf.units = "imperial"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data_imperial

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert "clear sky" in result
        assert "68.9F" in result
        assert "59.4F" in result
        assert "65%" in result
        mock_fetch_owm.assert_called_once_with(
            37.7749, -122.4194, units="imperial", exclude="minutely,hourly"
        )

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.weather.own_util.fetch_openweathermap")
    def test_process_success_with_wind_gust(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data_with_gust,
    ):
        """Test weather response includes wind gust when available."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_conf.units = "metric"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data_with_gust

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        # Note: Format uses {:.0f} which removes decimals
        assert "G25" in result  # Wind gust should be included (no decimal)
        assert "15@270" in result  # Wind speed and direction (no decimal)
        assert "partly cloudy" in result

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.weather.own_util.fetch_openweathermap")
    def test_process_success_without_wind_gust(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data_metric,
    ):
        """Test weather response without wind gust."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_conf.units = "metric"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data_metric

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert "G" not in result  # No gust indicator
        # Note: Format uses {:.0f} which removes decimals
        assert "10@180" in result  # Wind speed and direction only (no decimal)

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.weather.own_util.fetch_openweathermap")
    def test_process_success_with_callsign_in_message(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data_metric,
    ):
        """Test successful weather fetch with callsign in message."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_conf.units = "metric"
        mock_packet.get = Mock(
            side_effect=lambda key, default=None: {
                "from_call": "TESTCALL",
                "message_text": "weather OTHERCALL",
            }.get(key, default)
        )
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data_metric

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert "clear sky" in result
        mock_get_aprs_fi.assert_called_once_with("test_aprs_fi_key", "OTHERCALL")

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.weather.own_util.fetch_openweathermap")
    def test_process_success_with_lowercase_callsign(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data_metric,
    ):
        """Test that callsign is converted to uppercase."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_conf.units = "metric"
        mock_packet.get = Mock(
            side_effect=lambda key, default=None: {
                "from_call": "TESTCALL",
                "message_text": "weather othercall",
            }.get(key, default)
        )
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data_metric

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert "clear sky" in result
        mock_get_aprs_fi.assert_called_once_with("test_aprs_fi_key", "OTHERCALL")

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd_openweathermap_plugin.weather.plugin_utils.get_aprs_fi")
    def test_process_aprs_fi_exception(
        self,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
    ):
        """Test handling of aprs.fi API exception."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_get_aprs_fi.side_effect = Exception("API Error")

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert result == "Failed to fetch location"
        mock_get_aprs_fi.assert_called_once()

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd_openweathermap_plugin.weather.plugin_utils.get_aprs_fi")
    def test_process_empty_aprs_fi_entries(
        self,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
    ):
        """Test handling of empty aprs.fi entries."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_get_aprs_fi.return_value = {"entries": []}

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert result == "Failed to fetch location"
        mock_get_aprs_fi.assert_called_once()

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.weather.own_util.fetch_openweathermap")
    def test_process_owm_exception(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
    ):
        """Test handling of OpenWeatherMap API exception."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_conf.units = "metric"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.side_effect = Exception("OWM API Error")

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert result == "Unable to get weather"
        mock_fetch_owm.assert_called_once_with(
            37.7749, -122.4194, units="metric", exclude="minutely,hourly"
        )

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.weather.own_util.fetch_openweathermap")
    def test_process_various_weather_conditions(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
    ):
        """Test various weather conditions."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_conf.units = "metric"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data

        weather_conditions = [
            "light rain",
            "heavy snow",
            "fog",
            "thunderstorm",
            "scattered clouds",
        ]

        for condition in weather_conditions:
            mock_fetch_owm.return_value = {
                "current": {
                    "weather": [{"description": condition}],
                    "temp": 20.0,
                    "dew_point": 15.0,
                    "wind_speed": 10.0,
                    "wind_deg": 180,
                    "humidity": 65,
                }
            }

            # Execute
            result = plugin.process(mock_packet)

            # Verify
            assert condition in result

    @patch("aprsd_openweathermap_plugin.weather.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.weather.own_util.fetch_openweathermap")
    def test_process_message_text_none(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data_metric,
    ):
        """Test handling when message_text is None."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_conf.units = "metric"
        mock_packet.get = Mock(
            side_effect=lambda key, default=None: {
                "from_call": "TESTCALL",
                "message_text": None,
            }.get(key, default)
        )
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data_metric

        # Execute - the code doesn't handle None message_text gracefully
        # It will raise TypeError when re.search() is called with None
        with pytest.raises(TypeError, match="expected string or bytes-like object"):
            plugin.process(mock_packet)

    def test_setup(self, plugin):
        """Test setup method."""
        with (
            patch.object(plugin, "ensure_aprs_fi_key") as mock_aprs_fi,
            patch.object(plugin, "ensure_owm_key") as mock_owm,
        ):
            plugin.setup()
            mock_aprs_fi.assert_called_once()
            mock_owm.assert_called_once()

    def test_help(self, plugin):
        """Test help method."""
        help_text = plugin.help()
        assert isinstance(help_text, list)
        assert len(help_text) == 2
        assert "openweathermap" in help_text[0].lower()
        assert plugin.command_regex in help_text[0]

    def test_command_regex(self, plugin):
        """Test command regex matching."""
        import re

        regex = re.compile(plugin.command_regex)
        assert regex.match("w")
        assert regex.match("W")
        assert regex.match("weather")
        assert regex.match("Weather")
        assert regex.match("WEATHER")
        assert regex.match("weather CALLSIGN")
        assert not regex.match("time")
        assert not regex.match("other")

    def test_command_name(self, plugin):
        """Test command name."""
        assert plugin.command_name == "OpenWeatherMap"

    def test_short_description(self, plugin):
        """Test short description."""
        assert "weather" in plugin.short_description.lower()
        assert "openweathermap" in plugin.short_description.lower()
