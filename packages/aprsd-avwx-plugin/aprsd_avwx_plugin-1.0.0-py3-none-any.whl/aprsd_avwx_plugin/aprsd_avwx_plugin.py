import json
import logging
import re

from aprsd import plugin, plugin_utils
from aprsd.utils import trace
from oslo_config import cfg
import requests

import aprsd_avwx_plugin
from aprsd_avwx_plugin import conf  # noqa

CONF = cfg.CONF
LOG = logging.getLogger("APRSD")


class AVWXWeatherPlugin(plugin.APRSDRegexCommandPluginBase):
    """AVWXWeatherMap Weather Command

    Fetches a METAR weather report for the nearest
    weather station from the callsign
    Can be called with:
    metar - fetches metar for caller
    metar <CALLSIGN> - fetches metar for <CALLSIGN>

    This plugin requires the avwx-api service
    to provide the metar for a station near
    the callsign.

    avwx-api is an opensource project that has
    a hosted service here: https://avwx.rest/

    You can launch your own avwx-api in a container
    by cloning the githug repo here: https://github.com/avwx-rest/AVWX-API

    Then build the docker container with:
    docker build -f Dockerfile -t avwx-api:master .
    """

    version = aprsd_avwx_plugin.__version__
    command_regex = r"^([m]|[m]|[m]\s|metar)"
    command_name = "AVWXWeather"
    short_description = "AVWX weather of GPS Beacon location"

    def setup(self):
        if not CONF.avwx_plugin.base_url:
            LOG.error("Config avwx_plugin.base_url not specified.  Disabling")
            return False
        elif not CONF.avwx_plugin.apiKey:
            LOG.error("Config avwx_plugin.apiKey not specified. Disabling")
            return False

        self.enabled = True

    def help(self):
        _help = [
            f"avwxweather: Send {self.command_regex} to get weather from your location",
            f"avwxweather: Send {self.command_regex} <callsign> to get weather from <callsign>",
        ]
        return _help

    @trace.trace
    def process(self, packet):
        fromcall = packet.get("from")
        message = packet.get("message_text", None)
        # ack = packet.get("msgNo", "0")
        LOG.info(f"AVWXWeather Plugin '{message}'")
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

        api_key = CONF.avwx_plugin.apiKey
        base_url = CONF.avwx_plugin.base_url
        token = f"TOKEN {api_key}"
        headers = {"Authorization": token}
        try:
            coord = f"{lat},{lon}"
            url = (
                f"{base_url}/api/station/near/{coord}?"
                "n=1&airport=false&reporting=true&format=json"
            )

            LOG.debug(f"Get stations near me '{url}'")
            response = requests.get(url, headers=headers)
        except Exception as ex:
            LOG.error(ex)
            raise Exception(f"Failed to get the weather '{ex}'") from ex
        else:
            wx_data = json.loads(response.text)

        # LOG.debug(wx_data)
        station = wx_data[0]["station"]["icao"]

        try:
            url = (
                f"{base_url}/api/metar/{station}?options=info,translate,summary"
                "&airport=true&reporting=true&format=json&onfail=cache"
            )

            LOG.debug(f"Get METAR '{url}'")
            response = requests.get(url, headers=headers)
        except Exception as ex:
            LOG.error(ex)
            raise Exception(f"Failed to get metar {ex}") from ex
        else:
            metar_data = json.loads(response.text)

        # LOG.debug(metar_data)
        return metar_data["raw"]
