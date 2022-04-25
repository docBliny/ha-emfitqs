from . import DOMAIN, EMFITQS_DEVICES
from homeassistant.helpers.entity import Entity
import logging

_LOGGER = logging.getLogger(__name__)

SENSOR_ICONS = {
    'presence': 'mdi:hotel',
}

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Emfit QS binary sensor platform."""
    devices = []
    for device in hass.data[EMFITQS_DEVICES]:
        devices.append(EmfitQSPresenceSensor(device))

    add_devices(devices)

class EmfitQSBinarySensor(Entity):
    """Representation of an Emfit QS Binary Sensor."""
    def __init__(self, device, sensor_type):
        """Initialize the sensor."""
        self._device = device
        self._name = None
        self._old_value = None
        self._sensor_type = sensor_type

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        self.hass.async_add_executor_job(
            self._device.add_message_listener, self.on_message)

    async def async_will_remove_from_hass(self):
        """Call when entity is about to be removed from hass."""
        self.hass.async_add_executor_job(
            self._device.remove_message_listener, self.on_message)

    def on_message(self, message):
        """Handle new messages which are received from the device."""
        _LOGGER.debug("Message received for {}".format(self.name))
        # Prevent refreshing if not needed
        if self._old_value is None or self._old_value != self.state:
            self._old_value = self.state
            self.schedule_update_ha_state()

    @property
    def device_info(self):
        return {
            'identifiers': {
                (DOMAIN, self._device.serial_number, self._sensor_type)
            },
            'name': self._device.name,
            'manufacturer': "Emfit Ltd",
            'model': "Emfit QS",
            'sw_version': self._device.firmware_version,
        }

    @property
    def icon(self):
        """Return the icon for this sensor."""
        return SENSOR_ICONS[self._sensor_type]

    @property
    def name(self):
        """Return the name of the Emfit QS device."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def unique_id(self):
        """Return the sensor's unique id."""
        return '{}_{}'.format(self._device.serial_number, self._sensor_type)

class EmfitQSPresenceSensor(EmfitQSBinarySensor):
    """Representation of Emfit QS presence sensor."""

    def __init__(self, device):
        """Create a new Emfit QS presence sensor."""
        super().__init__(device, 'presence')
        self._name = "Emfit QS {} Presence".format(self._device.name)

    @property
    def state(self) -> bool:
        """Return presence value."""
        return self._device.presence
