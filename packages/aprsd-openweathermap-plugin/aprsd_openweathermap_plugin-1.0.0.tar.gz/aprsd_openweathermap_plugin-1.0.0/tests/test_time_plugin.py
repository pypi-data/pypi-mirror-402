"""Unit tests for TimePlugin."""

from unittest.mock import Mock, patch

import pytest
import pytz
from aprsd.packets import core

from aprsd_openweathermap_plugin.time import TimePlugin


class TestTimePlugin:
    """Test cases for TimePlugin."""

    @pytest.fixture
    def plugin(self):
        """Create a TimePlugin instance."""
        return TimePlugin()

    @pytest.fixture
    def mock_packet(self):
        """Create a mock packet."""
        packet = Mock(spec=core.Packet)
        packet.from_call = "TESTCALL"
        packet.message_text = "time"
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
    def mock_owm_data(self):
        """Mock OpenWeatherMap API response."""
        return {
            "timezone": "America/Los_Angeles",
        }

    @patch("aprsd_openweathermap_plugin.time.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.time.own_util.fetch_openweathermap")
    def test_process_success_with_from_call(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data,
    ):
        """Test successful time fetch using from_call."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data
        plugin.build_date_str = Mock(return_value="2024-01-01 12:00:00 PST")

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert result == "2024-01-01 12:00:00 PST"
        mock_get_aprs_fi.assert_called_once_with("test_aprs_fi_key", "TESTCALL")
        mock_fetch_owm.assert_called_once_with(37.7749, -122.4194)
        plugin.build_date_str.assert_called_once()
        # Verify timezone passed to build_date_str
        call_args = plugin.build_date_str.call_args[0][0]
        assert call_args == pytz.timezone("America/Los_Angeles")

    @patch("aprsd_openweathermap_plugin.time.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.time.own_util.fetch_openweathermap")
    def test_process_success_with_callsign_in_message(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data,
    ):
        """Test successful time fetch with callsign in message."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_packet.message_text = "time OTHERCALL"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data
        plugin.build_date_str = Mock(return_value="2024-01-01 12:00:00 PST")

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert result == "2024-01-01 12:00:00 PST"
        mock_get_aprs_fi.assert_called_once_with("test_aprs_fi_key", "OTHERCALL")
        mock_fetch_owm.assert_called_once_with(37.7749, -122.4194)

    @patch("aprsd_openweathermap_plugin.time.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.time.own_util.fetch_openweathermap")
    def test_process_success_with_lowercase_callsign(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data,
    ):
        """Test that callsign is converted to uppercase."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_packet.message_text = "time othercall"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data
        plugin.build_date_str = Mock(return_value="2024-01-01 12:00:00 PST")

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert result == "2024-01-01 12:00:00 PST"
        mock_get_aprs_fi.assert_called_once_with("test_aprs_fi_key", "OTHERCALL")

    @patch("aprsd_openweathermap_plugin.time.CONF")
    @patch("aprsd_openweathermap_plugin.time.plugin_utils.get_aprs_fi")
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

    @patch("aprsd_openweathermap_plugin.time.CONF")
    @patch("aprsd_openweathermap_plugin.time.plugin_utils.get_aprs_fi")
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
        assert result == "Failed to fetch aprs.fi location"
        mock_get_aprs_fi.assert_called_once()

    @patch("aprsd_openweathermap_plugin.time.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.time.own_util.fetch_openweathermap")
    def test_process_owm_exception_defaults_to_utc(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
    ):
        """Test that OpenWeatherMap exception defaults to UTC timezone."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.side_effect = Exception("OWM API Error")
        plugin.build_date_str = Mock(return_value="2024-01-01 12:00:00 UTC")

        # Execute
        result = plugin.process(mock_packet)

        # Verify
        assert result == "2024-01-01 12:00:00 UTC"
        mock_fetch_owm.assert_called_once_with(37.7749, -122.4194)
        plugin.build_date_str.assert_called_once()
        # Verify UTC timezone passed to build_date_str
        call_args = plugin.build_date_str.call_args[0][0]
        assert call_args == pytz.timezone("UTC")

    @patch("aprsd_openweathermap_plugin.time.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.time.own_util.fetch_openweathermap")
    def test_process_different_timezones(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
    ):
        """Test with different timezones from OpenWeatherMap."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        plugin.build_date_str = Mock(return_value="2024-01-01 12:00:00")

        timezones = [
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
        ]

        for tz in timezones:
            mock_fetch_owm.return_value = {"timezone": tz}
            plugin.build_date_str.reset_mock()

            # Execute
            result = plugin.process(mock_packet)

            # Verify
            assert result == "2024-01-01 12:00:00"
            call_args = plugin.build_date_str.call_args[0][0]
            assert call_args == pytz.timezone(tz)

    @patch("aprsd_openweathermap_plugin.time.CONF")
    @patch("aprsd.plugin_utils.get_aprs_fi")
    @patch("aprsd_openweathermap_plugin.time.own_util.fetch_openweathermap")
    def test_process_various_message_formats(
        self,
        mock_fetch_owm,
        mock_get_aprs_fi,
        mock_conf,
        plugin,
        mock_packet,
        mock_aprs_fi_data,
        mock_owm_data,
    ):
        """Test various message text formats."""
        # Setup mocks
        mock_conf.aprs_fi.apiKey = "test_aprs_fi_key"
        mock_get_aprs_fi.return_value = mock_aprs_fi_data
        mock_fetch_owm.return_value = mock_owm_data
        plugin.build_date_str = Mock(return_value="2024-01-01 12:00:00 PST")

        # Test different message formats
        # Note: The regex r"^.*\s+(.*)" requires a space followed by text
        # "t" or "time" without space uses fromcall
        # "t " or "time " with trailing space matches but group(1) is empty string
        test_cases = [
            ("t", "TESTCALL"),  # Single 't' - no match, uses fromcall
            ("t ", ""),  # 't' with space - matches but group(1) is empty
            ("time", "TESTCALL"),  # 'time' - no match, uses fromcall
            ("time CALLSIGN", "CALLSIGN"),  # 'time' with callsign
            ("t CALLSIGN", "CALLSIGN"),  # 't' with callsign
        ]

        for message, expected_callsign in test_cases:
            mock_packet.message_text = message
            mock_get_aprs_fi.reset_mock()
            plugin.build_date_str.reset_mock()

            # Execute
            result = plugin.process(mock_packet)

            # Verify
            assert result == "2024-01-01 12:00:00 PST"
            mock_get_aprs_fi.assert_called_once_with(
                "test_aprs_fi_key", expected_callsign
            )

    def test_setup(self, plugin):
        """Test setup method."""
        with (
            patch.object(plugin, "ensure_aprs_fi_key") as mock_aprs_fi,
            patch.object(plugin, "ensure_owm_key") as mock_owm,
        ):
            plugin.setup()
            mock_aprs_fi.assert_called_once()
            mock_owm.assert_called_once()

    def test_command_regex(self, plugin):
        """Test command regex matching."""
        import re

        regex = re.compile(plugin.command_regex)
        assert regex.match("t")
        assert regex.match("t ")
        assert regex.match("time")
        assert regex.match("time CALLSIGN")
        assert not regex.match("weather")
        assert not regex.match("other")

    def test_command_name(self, plugin):
        """Test command name."""
        assert plugin.command_name == "time"

    def test_short_description(self, plugin):
        """Test short description."""
        assert "timezone" in plugin.short_description.lower()
        assert "openweathermap" in plugin.short_description.lower()
