import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL,
)

class EcowaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecowater Hydrolink Custom."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Stap die wordt aangeroepen als de gebruiker de integratie toevoegt."""
        errors = {}

        if user_input is not None:
            # Hier maken we de entry aan (nog zonder validatie)
            return self.async_create_entry(
                title="Ecowater Hydrolink Custom",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        SCAN_INTERVAL_MINUTES, default=DEFAULT_SCAN_INTERVAL
                    ): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Koppel de opties flow."""
        return EcowaterOptionsFlowHandler(config_entry)


class EcowaterOptionsFlowHandler(config_entries.OptionsFlow):
    """Handelt de opties af na installatie."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        # Geen toewijzing aan self.config_entry! De basisklasse stelt die property al beschikbaar.
        pass

    async def async_step_init(self, user_input=None):
        """Beheer de opties."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Bepaal de standaardwaarde voor de scan interval
        # Eerst uit options, dan uit data, anders de default
        current_value = self.config_entry.options.get(
            SCAN_INTERVAL_MINUTES,
            self.config_entry.data.get(SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL)
        )

        data_schema = vol.Schema(
            {
                vol.Optional(SCAN_INTERVAL_MINUTES, default=current_value): int,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )