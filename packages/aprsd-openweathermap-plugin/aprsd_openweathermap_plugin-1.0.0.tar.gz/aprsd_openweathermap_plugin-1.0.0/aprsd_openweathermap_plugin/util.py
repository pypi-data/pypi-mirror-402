import json
import logging

import requests
from oslo_config import cfg

CONF = cfg.CONF
LOG = logging.getLogger("APRSD")


class OWMAPIKEYMixin:
    """Mixin class to enable checking the existence of the OpenWeatherMap apiKey."""

    def ensure_owm_key(self):
        if not CONF.aprsd_openweathermap_plugin.apiKey:
            LOG.error("Config aprsd_openweathermap_plugin.apiKey is not set")
            self.enabled = False
        else:
            self.enabled = True


def fetch_openweathermap(lat, lon, units="metric", exclude=None):
    """Fetch openweathermap for a given latitude and longitude."""
    api_key = CONF.aprsd_openweathermap_plugin.apiKey
    LOG.debug(f"Fetch openweathermap for {lat}, {lon}")
    if not exclude:
        exclude = "minutely,hourly,daily,alerts"
    try:
        url = (
            "https://api.openweathermap.org/data/3.0/onecall?"
            "lat={}&lon={}&appid={}&units={}&exclude={}".format(
                lat,
                lon,
                api_key,
                units,
                exclude,
            )
        )
        LOG.debug(f"Fetching OWM weather '{url}'")
        response = requests.get(url)
    except Exception as e:
        LOG.error(e)
        raise Exception("Failed to get weather") from e
    else:
        response.raise_for_status()
        return json.loads(response.text)
