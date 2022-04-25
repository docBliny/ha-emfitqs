from decimal import Decimal
from . import DOMAIN, EMFITQS_DEVICES
from homeassistant.helpers.entity import Entity
import logging

_LOGGER = logging.getLogger(__name__)

SENSOR_UNITS = {
    'activity': None,
    'heart_rate': 'bpm',
    'respiratory_rate': 'bpm',
}

SENSOR_ICONS = {
    'activity': 'mdi:account-convert',
    'heart_rate': 'mdi:heart',
    'respiratory_rate': 'mdi:mix-cloud',
}

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Emfit QS sensor platform."""
    devices = []
    for device in hass.data[EMFITQS_DEVICES]:
        devices.append(EmfitQSActivitySensor(device))
        devices.append(EmfitQSHeartRateSensor(device))
        devices.append(EmfitQSRespiratoryRateSensor(device))

    add_devices(devices)

class EmfitQSSensor(Entity):
    """Representation of an Emfit QS Sensor."""
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
        # Prevent refreshing if not needed
        _LOGGER.debug("Message received for {}".format(self.name))
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
    def icon(self) -> str:
        """Return the icon for this sensor."""
        return SENSOR_ICONS[self._sensor_type]

    @property
    def name(self) -> str:
        """Return the name of the Emfit QS device."""
        return self._name

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit the value is expressed in."""
        return SENSOR_UNITS[self._sensor_type]

    @property
    def unique_id(self):
        """Return the sensor's unique id."""
        return '{}_{}'.format(self._device.serial_number, self._sensor_type)

class EmfitQSActivitySensor(EmfitQSSensor):
    """Representation of Emfit QS activity sensor."""

    def __init__(self, device):
        """Create a new Emfit QS activity sensor."""
        super().__init__(device, 'activity')
        self._name = "Emfit QS {} Activity".format(self._device.name)

    @property
    def state(self) -> int:
        """Return activity value."""
        return self._device.activity

class EmfitQSHeartRateSensor(EmfitQSSensor):
    """Representation of Emfit QS heart rate sensor."""

    def __init__(self, device):
        """Create a new Emfit QS heart rate sensor."""
        super().__init__(device, 'heart_rate')
        self._name = "Emfit QS {} Heart Rate".format(self._device.name)

    @property
    def state(self) -> int:
        """Return heart rate value."""
        return self._device.heart_rate

class EmfitQSRespiratoryRateSensor(EmfitQSSensor):
    """Representation of Emfit QS respiratory rate sensor."""

    def __init__(self, device):
        """Create a new Emfit QS respiratory rate sensor."""
        super().__init__(device, 'respiratory_rate')
        self._name = "Emfit QS {} Respiratory Rate".format(self._device.name)

    @property
    def state(self) -> Decimal:
        """Return respiratory rate value."""
        return self._device.respiratory_rate
