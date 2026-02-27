import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, UNIT_METRIC

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Stel sensorplatform in."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Setting up Ecowater sensors")

    entities = [
        EcoWaterSensor(coordinator, "last_update", "last_update", None, None, SensorDeviceClass.TIMESTAMP, None),
        EcoWaterSensor(coordinator, "salt_level_percent", "salt_level_percent", None, None, None, SensorStateClass.MEASUREMENT),
        EcoWaterSensor(coordinator, "salt_level_rounded", "salt_level_rounded", None, None, None, None),
        EcoWaterSensor(coordinator, "out_of_salt_days", "out_of_salt_days", "dagen", "dagen", None, None),
        EcoWaterSensor(coordinator, "low_salt_trip_days", "low_salt_trip_days", "dagen", "dagen", None, None),
        EcoWaterSensor(coordinator, "service_reminder", "service_reminder", None, None, None, None),
        EcoWaterSensor(coordinator, "water_used_today", "water_used_today", "L", "gal", SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "total_water_used", "total_water_used", "L", "gal", SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "water_available", "water_available", "L", "gal", SensorDeviceClass.WATER, None),
        EcoWaterSensor(coordinator, "current_flow", "current_flow", "L/min", "gpm", None, SensorStateClass.MEASUREMENT),
        EcoWaterSensor(coordinator, "avg_daily_use", "avg_daily_use", "L", "gal", SensorDeviceClass.WATER, None),
        EcoWaterSensor(coordinator, "hardness", "hardness", "gpg", "gpg", None, None),
        EcoWaterSensor(coordinator, "total_regens", "total_regens", "keer", "keer", None, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "manual_regens", "manual_regens", None, None, None, None),
        EcoWaterSensor(coordinator, "days_since_regen", "days_since_regen", "dagen", "dagen", None, None),
        EcoWaterSensor(coordinator, "avg_days_between_regens", "avg_days_between_regens", "dagen", "dagen", None, None),
        EcoWaterSensor(coordinator, "avg_salt_per_regen", "avg_salt_per_regen", "kg", "lbs", None, None),
        EcoWaterSensor(coordinator, "model", "model", None, None, None, None),
        EcoWaterSensor(coordinator, "serial", "serial", None, None, None, None),
        EcoWaterSensor(coordinator, "software_version", "software_version", None, None, None, None),
        EcoWaterSensor(coordinator, "rssi", "rssi", "dBm", "dBm", SensorDeviceClass.SIGNAL_STRENGTH, SensorStateClass.MEASUREMENT),
        EcoWaterSensor(coordinator, "wifi_ssid", "wifi_ssid", None, None, None, None),
        EcoWaterSensor(coordinator, "days_in_operation", "days_in_operation", "dagen", "dagen", None, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "power_outages", "power_outages", "keer", "keer", None, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "dealer_name", "dealer_name", None, None, None, None),
        EcoWaterSensor(coordinator, "dealer_phone", "dealer_phone", None, None, None, None),
        EcoWaterSensor(coordinator, "rock_removed_since_regen", "rock_removed_since_regen", "kg", "lbs", None, None),
        EcoWaterSensor(coordinator, "total_rock_removed", "total_rock_removed", "kg", "lbs", None, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "total_salt_use", "total_salt_use", "kg", "lbs", None, SensorStateClass.TOTAL_INCREASING),
        EcoWaterSensor(coordinator, "calculated_daily_use", "calculated_daily_use", "L", "gal", SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING),
    ]

    _LOGGER.debug("Aantal sensors om toe te voegen: %d", len(entities))
    async_add_entities(entities)
    _LOGGER.debug("Sensors toegevoegd aan Home Assistant")


class EcoWaterSensor(CoordinatorEntity, SensorEntity):
    """Vertegenwoordigt een Ecowater sensor."""

    # Icon mapping per sensor key
    _icon_map = {
        "last_update": "mdi:update",
        "salt_level_percent": "mdi:beaker",
        "salt_level_rounded": "mdi:beaker",
        "out_of_salt_days": "mdi:calendar-alert",
        "low_salt_trip_days": "mdi:calendar-alert",
        "service_reminder": "mdi:bell",
        "water_used_today": "mdi:water",
        "total_water_used": "mdi:water-counter",
        "water_available": "mdi:water-percent",
        "current_flow": "mdi:water",
        "avg_daily_use": "mdi:chart-line",
        "hardness": "mdi:flask",
        "total_regens": "mdi:counter",
        "manual_regens": "mdi:counter",
        "days_since_regen": "mdi:calendar",
        "avg_days_between_regens": "mdi:calendar",
        "avg_salt_per_regen": "mdi:scale",
        "model": "mdi:chip",
        "serial": "mdi:information-outline",
        "software_version": "mdi:information-outline",
        "rssi": "mdi:wifi",
        "wifi_ssid": "mdi:wifi",
        "days_in_operation": "mdi:calendar",
        "power_outages": "mdi:flash",
        "dealer_name": "mdi:phone",
        "dealer_phone": "mdi:phone",
        "rock_removed_since_regen": "mdi:weight",
        "total_rock_removed": "mdi:weight",
        "total_salt_use": "mdi:weight",
        "calculated_daily_use": "mdi:calculator",
    }

    def __init__(self, coordinator, trans_key, data_key, unit_metric, unit_imperial, device_class, state_class):
        super().__init__(coordinator)
        self._attr_translation_key = trans_key
        self._attr_has_entity_name = True
        self._key = data_key
        self._unit_metric = unit_metric
        self._unit_imperial = unit_imperial
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
    def icon(self):
        """Bepaal het icoon op basis van de sensor key."""
        return self._icon_map.get(self._key, "mdi:help")

    @property
    def native_value(self):
        """Geef de huidige waarde van de sensor."""
        if self.coordinator.data:
            value = self.coordinator.data.get(self._key)
            _LOGGER.debug("Sensor %s: key=%s, value=%s", self.entity_id, self._key, value)
            return value
        _LOGGER.debug("Sensor %s: coordinator.data is None", self.entity_id)
        return None

    @property
    def native_unit_of_measurement(self):
        """Bepaal de eenheid op basis van het gekozen eenheidssysteem."""
        if self._unit_metric is None:
            return None
        if self.coordinator.unit_system == UNIT_METRIC:
            unit = self._unit_metric
        else:
            unit = self._unit_imperial
        _LOGGER.debug(
            "Sensor %s: unit_system=%s, _unit_metric=%s, _unit_imperial=%s, eenheid=%s",
            self.entity_id,
            self.coordinator.unit_system,
            self._unit_metric,
            self._unit_imperial,
            unit
        )
        return unit

    @property
    def extra_state_attributes(self):
        """Voeg de waarde in de alternatieve eenheid toe als attribuut (indien beschikbaar)."""
        attrs = {}
        if not self.coordinator.data:
            return attrs

        # Helper om alternatieve eenheid toe te voegen
        def add_alternate(key_metric, key_imperial, unit_metric, unit_imperial):
            metric = self.coordinator.data.get(key_metric)
            imperial = self.coordinator.data.get(key_imperial)
            if metric is None or imperial is None:
                return
            if self.coordinator.unit_system == UNIT_METRIC:
                attrs["imperial_value"] = imperial
                attrs["imperial_unit"] = unit_imperial
            else:
                attrs["metric_value"] = metric
                attrs["metric_unit"] = unit_metric

        if self._key == "rock_removed_since_regen":
            add_alternate("rock_removed_since_regen_metric", "rock_removed_since_regen_imperial", "kg", "lbs")
        elif self._key == "total_rock_removed":
            add_alternate("total_rock_removed_metric", "total_rock_removed_imperial", "kg", "lbs")
        elif self._key == "total_salt_use":
            add_alternate("total_salt_use_metric", "total_salt_use_imperial", "kg", "lbs")

        return attrs
