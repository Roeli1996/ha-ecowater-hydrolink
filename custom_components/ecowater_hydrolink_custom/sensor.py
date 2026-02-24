import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_USERNAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Stel sensorplatform in."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Setting up Ecowater sensors")

    entities = [
        EcoWaterSensor(coordinator, "last_update", "last_update", None, SensorDeviceClass.TIMESTAMP, None),
        EcoWaterSensor(coordinator, "salt_level_percent", "salt_level_percent", "%", None, SensorStateClass.MEASUREMENT),
        EcoWaterSensor(coordinator, "salt_level_rounded", "salt_level_rounded", "%", None, None),
        EcoWaterSensor(coordinator, "out_of_salt_days", "out_of_salt_days", "dagen", None, None),
        EcoWaterSensor(coordinator, "low_salt_trip_days", "low_salt_trip_days", "dagen", None, None),
        EcoWaterSensor(coordinator, "service_reminder", "service_reminder", None, None, None),
        EcoWaterSensor(coordinator, "water_used_today", "water_used_today", "L", SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "total_water_used", "total_water_used", "L", SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "water_available", "water_available", "L", SensorDeviceClass.WATER, None),
        EcoWaterSensor(coordinator, "current_flow", "current_flow", "L/min", None, SensorStateClass.MEASUREMENT),
        EcoWaterSensor(coordinator, "avg_daily_use", "avg_daily_use", "L", SensorDeviceClass.WATER, None),
        EcoWaterSensor(coordinator, "hardness", "hardness", "gpg", None, None),
        EcoWaterSensor(coordinator, "total_regens", "total_regens", "keer", None, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "manual_regens", "manual_regens", "keer", None, None),
        EcoWaterSensor(coordinator, "days_since_regen", "days_since_regen", "dagen", None, None),
        EcoWaterSensor(coordinator, "avg_days_between_regens", "avg_days_between_regens", "dagen", None, None),
        EcoWaterSensor(coordinator, "avg_salt_per_regen", "avg_salt_per_regen", "kg", None, None),
        EcoWaterSensor(coordinator, "model", "model", None, None, None),
        EcoWaterSensor(coordinator, "serial", "serial", None, None, None),
        EcoWaterSensor(coordinator, "software_version", "software_version", None, None, None),
        EcoWaterSensor(coordinator, "rssi", "rssi", "dBm", SensorDeviceClass.SIGNAL_STRENGTH, SensorStateClass.MEASUREMENT),
        EcoWaterSensor(coordinator, "wifi_ssid", "wifi_ssid", None, None, None),
        EcoWaterSensor(coordinator, "days_in_operation", "days_in_operation", "dagen", None, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "power_outages", "power_outages", "keer", None, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "dealer_name", "dealer_name", None, None, None),
        EcoWaterSensor(coordinator, "dealer_phone", "dealer_phone", None, None, None),
    ]

    _LOGGER.debug("Aantal sensors om toe te voegen: %d", len(entities))
    async_add_entities(entities)
    _LOGGER.debug("Sensors toegevoegd aan Home Assistant")

class EcoWaterSensor(CoordinatorEntity, SensorEntity):
    """Vertegenwoordigt een Ecowater sensor."""

    def __init__(self, coordinator, trans_key, data_key, unit, device_class, state_class):
        super().__init__(coordinator)
        self._attr_translation_key = trans_key
        self._attr_has_entity_name = True
        self._key = data_key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = f"{DOMAIN}_{data_key}_{coordinator.entry.entry_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "Ecowater Waterontharder",
            "manufacturer": "EcoWater",
            "model": coordinator.data.get("model") if coordinator.data else None,
        }

    @property
    def native_value(self):
        """Geef de huidige waarde van de sensor."""
        if self.coordinator.data:
            value = self.coordinator.data.get(self._key)
            _LOGGER.debug("Sensor %s: key=%s, value=%s", self.entity_id, self._key, value)
            return value
        _LOGGER.debug("Sensor %s: coordinator.data is None", self.entity_id)
        return None