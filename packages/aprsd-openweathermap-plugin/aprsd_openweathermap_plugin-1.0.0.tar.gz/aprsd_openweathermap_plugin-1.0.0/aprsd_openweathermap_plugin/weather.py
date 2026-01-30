import logging
import re

from aprsd import plugin, plugin_utils
from aprsd.packets import core
from aprsd.utils import trace
from oslo_config import cfg

from aprsd_openweathermap_plugin import util as own_util
from aprsd_openweathermap_plugin.util import OWMAPIKEYMixin

CONF = cfg.CONF
LOG = logging.getLogger("APRSD")


class WeatherPlugin(
    plugin.APRSDRegexCommandPluginBase,
    OWMAPIKEYMixin,
    plugin.APRSFIKEYMixin,
):
    """OpenWeatherMap Weather Command

    This provides weather near the caller or callsign.

    How to Call: Send a message to aprsd
    "weather" - returns the weather near the calling callsign
    "weather CALLSIGN" - returns the weather near CALLSIGN

    This plugin uses the openweathermap API to fetch
    location and weather information.

    To use this plugin you need to get an openweathermap
    account and apikey.

    https://home.openweathermap.org/api_keys

    """

    # command_regex = r"^([w][x]|[w][x]\s|weather)"
    command_regex = r"^[wW]"

    command_name = "OpenWeatherMap"
    short_description = "OpenWeatherMap weather of GPS Beacon location"

    def setup(self):
        self.ensure_aprs_fi_key()
        self.ensure_owm_key()

    def help(self):
        _help = [
            "openweathermap: Send {} to get weather from your location".format(
                self.command_regex
            ),
            "openweathermap: Send {} <callsign> to get weather from <callsign>".format(
                self.command_regex
            ),
        ]
        return _help

    @trace.trace
    def process(self, packet: core.Packet):
        fromcall = packet.get("from_call")
        message = packet.get("message_text", None)
        # ack = packet.get("msgNo", "0")
        LOG.info(f"Weather Plugin '{message}'")
        a = re.search(r"^.*\s+(.*)", message)
        if a is not None:
            searchcall = a.group(1)
            searchcall = searchcall.upper()
        else:
            searchcall = fromcall

        api_key = CONF.aprs_fi.apiKey

        try:
            aprs_data = plugin_utils.get_aprs_fi(api_key, searchcall)
        except Exception as ex:
            LOG.error(f"Failed to fetch aprs.fi data {ex}")
            return "Failed to fetch location"

        # LOG.debug("LocationPlugin: aprs_data = {}".format(aprs_data))
        if not len(aprs_data["entries"]):
            LOG.error("Found no entries from aprs.fi!")
            return "Failed to fetch location"

        lat = aprs_data["entries"][0]["lat"]
        lon = aprs_data["entries"][0]["lng"]

        units = CONF.units
        try:
            wx_data = own_util.fetch_openweathermap(
                lat,
                lon,
                units=units,
                exclude="minutely,hourly",
            )
        except Exception as ex:
            LOG.error(f"Couldn't fetch openweathermap api '{ex}'")
            # default to UTC
            return "Unable to get weather"

        if units == "metric":
            degree = "C"
        else:
            degree = "F"

        if "wind_gust" in wx_data["current"]:
            wind = "{:.0f}@{}G{:.0f}".format(
                wx_data["current"]["wind_speed"],
                wx_data["current"]["wind_deg"],
                wx_data["current"]["wind_gust"],
            )
        else:
            wind = "{:.0f}@{}".format(
                wx_data["current"]["wind_speed"],
                wx_data["current"]["wind_deg"],
            )

        # LOG.debug(wx_data["current"])
        # LOG.debug(wx_data["daily"])
        reply = "{} {:.1f}{}/{:.1f}{} Wind {} {}%".format(
            wx_data["current"]["weather"][0]["description"],
            wx_data["current"]["temp"],
            degree,
            wx_data["current"]["dew_point"],
            degree,
            wind,
            wx_data["current"]["humidity"],
        )

        return reply
