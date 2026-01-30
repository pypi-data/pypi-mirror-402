import logging
import re

import pytz
from aprsd import plugin, plugin_utils
from aprsd.packets import core
from aprsd.plugins.time import TimePlugin
from aprsd.utils import trace
from oslo_config import cfg

from aprsd_openweathermap_plugin import util as own_util
from aprsd_openweathermap_plugin.util import OWMAPIKEYMixin

CONF = cfg.CONF
LOG = logging.getLogger("APRSD")


class TimePlugin(TimePlugin, plugin.APRSFIKEYMixin, OWMAPIKEYMixin):
    """OpenWeatherMap based timezone fetching."""

    command_regex = r"^([t]|[t]\s|time)"
    command_name = "time"
    short_description = "Current time of GPS beacon's timezone. Uses OpenWeatherMap"

    def setup(self):
        self.ensure_aprs_fi_key()
        self.ensure_owm_key()

    @trace.trace
    def process(self, packet: core.Packet):
        fromcall = packet.from_call
        message = packet.message_text
        # ack = packet.get("msgNo", "0")

        # optional second argument is a callsign to search
        a = re.search(r"^.*\s+(.*)", message)
        if a is not None:
            searchcall = a.group(1)
            searchcall = searchcall.upper()
        else:
            # if no second argument, search for calling station
            searchcall = fromcall

        api_key = CONF.aprs_fi.apiKey
        try:
            aprs_data = plugin_utils.get_aprs_fi(api_key, searchcall)
        except Exception as ex:
            LOG.error(f"Failed to fetch aprs.fi data {ex}")
            return "Failed to fetch location"

        LOG.debug(f"LocationPlugin: aprs_data = {aprs_data}")
        if not len(aprs_data["entries"]):
            LOG.error("Didn't get any entries from aprs.fi")
            return "Failed to fetch aprs.fi location"

        lat = aprs_data["entries"][0]["lat"]
        lon = aprs_data["entries"][0]["lng"]

        try:
            results = own_util.fetch_openweathermap(lat, lon)
        except Exception as ex:
            LOG.error(f"Couldn't fetch openweathermap api '{ex}'")
            # default to UTC
            localzone = pytz.timezone("UTC")
        else:
            tzone = results["timezone"]
            localzone = pytz.timezone(tzone)

        return self.build_date_str(localzone)
