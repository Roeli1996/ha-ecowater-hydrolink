import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, BACKEND_IQUA

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary_sensor platform from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Setting up Ecowater binary sensors")

    binary_sensors = [
        EcoWaterBinarySensor(coordinator, "is_regenerating", BinarySensorDeviceClass.RUNNING),
        EcoWaterBinarySensor(coordinator, "salt_alert", BinarySensorDeviceClass.PROBLEM),
        EcoWaterBinarySensor(coordinator, "leak_alert", BinarySensorDeviceClass.PROBLEM),
        EcoWaterBinarySensor(coordinator, "error_alert", BinarySensorDeviceClass.PROBLEM),
        EcoWaterBinarySensor(coordinator, "alarm_beeping", BinarySensorDeviceClass.SOUND),
    ]

    # The iQua backend reports an explicit online/offline device state that
    # Hydrolink does not expose.
    if getattr(coordinator, "backend", None) == BACKEND_IQUA:
        binary_sensors.append(
            EcoWaterBinarySensor(coordinator, "connectivity", BinarySensorDeviceClass.CONNECTIVITY)
        )

    _LOGGER.debug("Number of binary sensors to add: %d", len(binary_sensors))
    async_add_entities(binary_sensors)
    _LOGGER.debug("Binary sensors added to Home Assistant")


class EcoWaterBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of an Ecowater binary sensor."""

    # Icon mapping per binary sensor key
    _icon_map = {
        "is_regenerating": "mdi:refresh",
        "salt_alert": "mdi:alarm",
        "leak_alert": "mdi:pipe-leak",
        "error_alert": "mdi:alert-circle",
        "alarm_beeping": "mdi:bell-ring",
        "connectivity": "mdi:wifi",
    }

    def __init__(self, coordinator, data_key, device_class):
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_translation_key = data_key
        self._attr_has_entity_name = True
        self._attr_device_class = device_class
        self._attr_unique_id = f"{DOMAIN}_bin_{data_key}_{coordinator.entry.entry_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "Ecowater Water Softener",
            "manufacturer": "EcoWater",
            "model": coordinator.data.get("model") if coordinator.data else None,
        }

    @property
    def icon(self):
        """Return the icon to use in the frontend, based on the sensor key."""
        return self._icon_map.get(self._data_key, "mdi:help")

    @property
    def is_on(self):
        """Return True if the binary sensor is 'on'."""
        if self.coordinator.data:
            value = self.coordinator.data.get(self._data_key, False)
            _LOGGER.debug("Binary sensor %s: key=%s, value=%s", self.entity_id, self._data_key, value)
            return value
        _LOGGER.debug("Binary sensor %s: coordinator.data is None", self.entity_id)
        return False

    @property
    def available(self):
        """Return availability based on the coordinator."""
        return self.coordinator.last_update_success
