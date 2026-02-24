import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS
from .coordinator import EcowaterCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stel de Ecowater Hydrolink Custom integratie in vanuit een config entry."""

    # Maak de coordinator aan
    coordinator = EcowaterCoordinator(hass, entry)

    try:
        # Haal de eerste keer data op. Als dit faalt (bijv. geen internet),
        # markeert HA de integratie als 'niet gereed' en probeert het later opnieuw.
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        raise ConfigEntryNotReady(f"Fout bij eerste verbinding met Ecowater API: {ex}")

    # Sla de coordinator op in de centrale data-opslag van Home Assistant
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Start de platforms (sensor.py en binary_sensor.py)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Voeg een listener toe voor het geval je de opties (zoals scan_interval) aanpast
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Herlaad de integratie wanneer de opties worden gewijzigd via de UI."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verwijder de integratie en stop alle actieve processen."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Ruim de opgeslagen coordinator data op
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok