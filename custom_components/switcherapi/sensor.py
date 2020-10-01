"""Sensor platform for switcherapi."""
from custom_components.switcherapi.const import DEFAULT_NAME, DOMAIN, ICON, SENSOR
from custom_components.switcherapi.entity import SwitcherApiEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([SwitcherApiSensor(coordinator, entry)])


class SwitcherApiSensor(SwitcherApiEntity):
    """switcherapi Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SENSOR}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("static")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON
