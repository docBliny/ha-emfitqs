"""Support for Emfit QS sleep sensor"""
from homeassistant.const import CONF_HOSTS, CONF_ID, CONF_SCAN_INTERVAL
import homeassistant.helpers.config_validation as cv
import logging
from datetime import timedelta
from requests.exceptions import ConnectTimeout, HTTPError
import voluptuous as vol

DOMAIN = 'emfitqs'
# REQUIREMENTS = [
#     "requests==2.27.1"
# ]

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOSTS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_SCAN_INTERVAL): cv.positive_int
    }),
}, extra=vol.ALLOW_EXTRA)

EMFITQS_DEVICES = 'emfitqs_devices'
EMFITQS_PLATFORMS = ['binary_sensor', 'sensor']

_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    """ Setup Emfit QS device """
    if EMFITQS_DEVICES not in hass.data:
        hass.data[EMFITQS_DEVICES] = []

    conf = config[DOMAIN]
    scan_interval = conf.get(CONF_SCAN_INTERVAL, EmfitQS.DEFAULT_UPDATE_RATE)

    for host in conf[CONF_HOSTS]:
        try:
            device = EmfitQSDevice(host=host, update_rate=scan_interval)
            device.update()
            hass.data[EMFITQS_DEVICES].append(device)
        except (ConnectTimeout, HTTPError) as ex:
            _LOGGER.error("Unable to connect to EmfitQS device: %s", str(ex))

    # Save devices and start the platforms for each entity
    if hass.data[EMFITQS_DEVICES]:
        _LOGGER.debug("Starting platforms: {}".format(EMFITQS_PLATFORMS))
        for platform in EMFITQS_PLATFORMS:
            hass.helpers.discovery.load_platform(platform, DOMAIN, {}, config)

    return True

from .emfit_qs import EmfitQS
class EmfitQSDevice(EmfitQS):
    """Wrapper object to Emfit QS device."""

    def __init__(self, host: str, update_rate=None):
        """Initialize the wrapper object."""
        super().__init__(host, update_rate)

    @property
    def name(self) -> str:
        """Gets name of unit."""
        return self.serial_number
