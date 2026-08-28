"""Switch platform for Ecowater Hydrolink Custom integration.

Only the iQua backend exposes a controllable water shutoff valve; on the
Hydrolink backend this platform adds no entities.
"""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BACKEND_IQUA, IQUA_VALVE_OPEN, IQUA_VALVE_CLOSED

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch platform from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if getattr(coordinator, "backend", None) != BACKEND_IQUA:
        return

    async_add_entities([EcoWaterShutoffValveSwitch(coordinator)])


class EcoWaterShutoffValveSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the water shutoff valve as a switch.

    Disabled by default: closing the main water shutoff valve is a
    consequential physical action, so it requires an explicit opt-in from
    the user in the entity registry before it becomes active.
    """

    _attr_translation_key = "water_shutoff_valve"
    _attr_has_entity_name = True
    _attr_icon = "mdi:water-pump"
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_water_shutoff_valve_{coordinator.entry.entry_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": "Ecowater Water Softener",
            "manufacturer": "EcoWater",
            "model": coordinator.data.get("model") if coordinator.data else None,
        }

    @property
    def is_on(self):
        """Return True if the valve is open."""
        if self.coordinator.data:
            return self.coordinator.data.get("water_shutoff_valve_state") == IQUA_VALVE_OPEN
        return False

    @property
    def available(self):
        """Return False if the device has no shutoff valve, or is unreachable."""
        if not self.coordinator.last_update_success or not self.coordinator.data:
            return False
        state = self.coordinator.data.get("water_shutoff_valve_state")
        return state in (IQUA_VALVE_OPEN, IQUA_VALVE_CLOSED)

    async def async_turn_on(self, **kwargs):
        """Open the water shutoff valve."""
        await self.coordinator.async_set_water_shutoff_valve(IQUA_VALVE_OPEN)

    async def async_turn_off(self, **kwargs):
        """Close the water shutoff valve."""
        await self.coordinator.async_set_water_shutoff_valve(IQUA_VALVE_CLOSED)
