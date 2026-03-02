"""Sensor platform for Ecowater Hydrolink Custom integration.

This module defines all sensor entities. It handles dynamic units:
- Units that depend on the selected unit system (metric/imperial)
- Units that should be translated according to the Home Assistant language
  (e.g., "days", "times")
"""

import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, UNIT_METRIC

_LOGGER = logging.getLogger(__name__)

# Translation dictionaries for units that are language‑dependent.
# These are used for sensors like "out_of_salt_days", "total_regens", etc.
DAYS_UNIT_TRANSLATIONS = {
    "nl": "dagen",
    "en": "days",
    "fr": "jours",
    "de": "Tage",
    "es": "días",
    "it": "giorni",
    "pl": "dni",
    "pt": "dias",
}

TIMES_UNIT_TRANSLATIONS = {
    "nl": "keer",
    "en": "times",
    "fr": "fois",
    "de": "Mal",
    "es": "veces",
    "it": "volte",
    "pl": "razy",
    "pt": "vezes",
}


def get_days_unit(language):
    """Return the translated unit for "days" based on the Home Assistant language.

    Args:
        language: Two‑letter language code (e.g., "nl", "en").

    Returns:
        Translated unit string, or "days" as fallback.
    """
    return DAYS_UNIT_TRANSLATIONS.get(language, "days")


def get_times_unit(language):
    """Return the translated unit for "times" based on the Home Assistant language.

    Args:
        language: Two‑letter language code (e.g., "nl", "en").

    Returns:
        Translated unit string, or "times" as fallback.
    """
    return TIMES_UNIT_TRANSLATIONS.get(language, "times")


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform from a config entry.

    Args:
        hass: HomeAssistant instance.
        entry: ConfigEntry containing user configuration.
        async_add_entities: Callback to add entities.
    """
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Setting up Ecowater sensors")

    entities = [
        # Timestamp sensor
        EcoWaterSensor(
            coordinator, "last_update", "last_update",
            None, None, SensorDeviceClass.TIMESTAMP, None
        ),
        # Salt level sensors
        EcoWaterSensor(
            coordinator, "salt_level_percent", "salt_level_percent",
            None, None, None, SensorStateClass.MEASUREMENT
        ),
        EcoWaterSensor(
            coordinator, "salt_level_rounded", "salt_level_rounded",
            None, None, None, None
        ),
        # Day‑based sensors (units are language‑dependent)
        EcoWaterSensor(
            coordinator, "out_of_salt_days", "out_of_salt_days",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "low_salt_trip_days", "low_salt_trip_days",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "service_reminder", "service_reminder",
            None, None, None, None
        ),
        # Unit‑system‑dependent sensors (metric/imperial)
        EcoWaterSensor(
            coordinator, "water_used_today", "water_used_today",
            "L", "gal", SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING
        ),
        EcoWaterSensor(
            coordinator, "total_water_used", "total_water_used",
            "L", "gal", SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING
        ),
        EcoWaterSensor(
            coordinator, "water_available", "water_available",
            "L", "gal", SensorDeviceClass.WATER, None
        ),
        EcoWaterSensor(
            coordinator, "current_flow", "current_flow",
            "L/min", "gpm", None, SensorStateClass.MEASUREMENT
        ),
        EcoWaterSensor(
            coordinator, "avg_daily_use", "avg_daily_use",
            "L", "gal", SensorDeviceClass.WATER, None
        ),
        EcoWaterSensor(
            coordinator, "hardness", "hardness",
            "gpg", "gpg", None, None
        ),
        # Count‑based sensors (units are language‑dependent: "keer"/"times")
        EcoWaterSensor(
            coordinator, "total_regens", "total_regens",
            None, None, None, SensorStateClass.TOTAL_INCREASING
        ),
        EcoWaterSensor(
            coordinator, "manual_regens", "manual_regens",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "days_since_regen", "days_since_regen",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "avg_days_between_regens", "avg_days_between_regens",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "avg_salt_per_regen", "avg_salt_per_regen",
            "kg", "lbs", None, None
        ),
        # Device information sensors
        EcoWaterSensor(
            coordinator, "model", "model",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "serial", "serial",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "software_version", "software_version",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "rssi", "rssi",
            "dBm", "dBm", SensorDeviceClass.SIGNAL_STRENGTH, SensorStateClass.MEASUREMENT
        ),
        EcoWaterSensor(
            coordinator, "wifi_ssid", "wifi_ssid",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "days_in_operation", "days_in_operation",
            None, None, None, SensorStateClass.TOTAL_INCREASING
        ),
        EcoWaterSensor(
            coordinator, "power_outages", "power_outages",
            None, None, None, SensorStateClass.TOTAL_INCREASING
        ),
        EcoWaterSensor(
            coordinator, "dealer_name", "dealer_name",
            None, None, None, None
        ),
        EcoWaterSensor(
            coordinator, "dealer_phone", "dealer_phone",
            None, None, None, None
        ),
        # Additional sensors (weight, calculated daily usage)
        EcoWaterSensor(
            coordinator, "rock_removed_since_regen", "rock_removed_since_regen",
            "kg", "lbs", None, None
        ),
        EcoWaterSensor(
            coordinator, "total_rock_removed", "total_rock_removed",
            "kg", "lbs", None, SensorStateClass.TOTAL_INCREASING
        ),
        EcoWaterSensor(
            coordinator, "total_salt_use", "total_salt_use",
            "kg", "lbs", None, SensorStateClass.TOTAL_INCREASING
        ),
        EcoWaterSensor(
            coordinator, "calculated_daily_use", "calculated_daily_use",
            "L", "gal", SensorDeviceClass.WATER, SensorStateClass.TOTAL_INCREASING
        ),
    ]

    _LOGGER.debug("Number of sensors to add: %d", len(entities))
    async_add_entities(entities)
    _LOGGER.debug("Sensors added to Home Assistant")


class EcoWaterSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Ecowater sensor.

    This class handles:
    - Dynamic unit display (metric/imperial or language‑dependent)
    - Icons based on sensor type
    - Extra attributes (alternative unit values)
    """

    # Icon mapping per sensor key – chosen from Material Design Icons
    _icon_map = {
        "last_update": "mdi:update",
        "salt_level_percent": "mdi:beaker",
        "salt_level_rounded": "mdi:beaker",
        "out_of_salt_days": "mdi:calendar-alert",
        "low_salt_trip_days": "mdi:calendar-alert",
        "service_reminder": "mdi:bell",
        "water_used_today": "mdi:water",
        "total_water_used": "mdi:water",
        "water_available": "mdi:water-percent",
        "current_flow": "mdi:water-pump",
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
        """Initialize the sensor.

        Args:
            coordinator: The EcowaterCoordinator instance.
            trans_key: Translation key for the entity name.
            data_key: Key in the coordinator.data dictionary.
            unit_metric: Unit string to use when metric system is selected (or None if not applicable).
            unit_imperial: Unit string to use when imperial system is selected (or None if not applicable).
            device_class: Home Assistant device class (if any).
            state_class: Home Assistant state class (if any).
        """
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
            "name": "Ecowater Water Softener",
            "manufacturer": "EcoWater",
            "model": coordinator.data.get("model") if coordinator.data else None,
        }

    @property
    def icon(self):
        """Return the icon to use in the frontend, based on the sensor key."""
        return self._icon_map.get(self._key, "mdi:help")

    @property
    def native_value(self):
        """Return the current sensor value."""
        if self.coordinator.data:
            value = self.coordinator.data.get(self._key)
            _LOGGER.debug("Sensor %s: key=%s, value=%s", self.entity_id, self._key, value)
            return value
        _LOGGER.debug("Sensor %s: coordinator.data is None", self.entity_id)
        return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement.

        The unit is determined as follows:
        - For day‑based sensors (e.g., out_of_salt_days): translated based on HA language.
        - For count‑based sensors (total_regens, power_outages): translated based on HA language.
        - For other sensors: depends on the selected unit system (metric/imperial).
        """
        # Day‑based sensors (language‑dependent)
        if self._key in [
            "out_of_salt_days", "low_salt_trip_days",
            "days_since_regen", "avg_days_between_regens",
            "days_in_operation"
        ]:
            unit = get_days_unit(self.coordinator.language)
            _LOGGER.debug(
                "Sensor %s: language=%s, days unit=%s",
                self.entity_id, self.coordinator.language, unit
            )
            return unit

        # Count‑based sensors (language‑dependent)
        if self._key in ["total_regens", "power_outages"]:
            unit = get_times_unit(self.coordinator.language)
            _LOGGER.debug(
                "Sensor %s: language=%s, times unit=%s",
                self.entity_id, self.coordinator.language, unit
            )
            return unit

        # All other sensors: use the unit system (if applicable)
        if self._unit_metric is None:
            return None
        if self.coordinator.unit_system == UNIT_METRIC:
            unit = self._unit_metric
        else:
            unit = self._unit_imperial
        _LOGGER.debug(
            "Sensor %s: unit_system=%s, _unit_metric=%s, _unit_imperial=%s, unit=%s",
            self.entity_id,
            self.coordinator.unit_system,
            self._unit_metric,
            self._unit_imperial,
            unit,
        )
        return unit

    @property
    def extra_state_attributes(self):
        """Return extra state attributes.

        For weight‑related sensors (rock, total rock, total salt), the value in the
        alternative unit (metric/imperial) is exposed as an attribute.
        """
        attrs = {}
        if not self.coordinator.data:
            return attrs

        # Helper to add the alternative unit value
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
            add_alternate(
                "rock_removed_since_regen_metric",
                "rock_removed_since_regen_imperial",
                "kg", "lbs"
            )
        elif self._key == "total_rock_removed":
            add_alternate(
                "total_rock_removed_metric",
                "total_rock_removed_imperial",
                "kg", "lbs"
            )
        elif self._key == "total_salt_use":
            add_alternate(
                "total_salt_use_metric",
                "total_salt_use_imperial",
                "kg", "lbs"
            )

        return attrs
