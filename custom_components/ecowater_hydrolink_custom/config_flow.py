"""Config flow for Ecowater Hydrolink Custom integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_REGION,
    REGION_EU,
    REGION_US,
    SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class EcowaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecowater Hydrolink Custom."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Step called when the user adds the integration."""
        errors = {}

        if user_input is not None:
            # Create the entry with the selected region
            return self.async_create_entry(
                title="Ecowater Hydrolink Custom",
                data=user_input
            )

        # Schema with region selection
        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_REGION, default=REGION_EU): vol.In(
                    {
                        REGION_EU: "Europe (app.hydrolinkhome.eu)",
                        REGION_US: "US / Other (app.hydrolinkhome.com)",
                    }
                ),
                vol.Optional(
                    SCAN_INTERVAL_MINUTES, default=DEFAULT_SCAN_INTERVAL
                ): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return EcowaterOptionsFlowHandler(config_entry)

    async def async_migrate_entry(self, hass, config_entry: config_entries.ConfigEntry):
        """Migrate old entry."""
        _LOGGER.debug("Migrating from version %s", config_entry.version)

        if config_entry.version == 1:
            # Version 1 had no region; add EU as default
            new_data = {**config_entry.data}
            new_data[CONF_REGION] = REGION_EU
            config_entry.version = 2
            hass.config_entries.async_update_entry(config_entry, data=new_data)
            _LOGGER.debug("Migration to version 2 complete")

        return True


class EcowaterOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options after installation."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        pass

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Determine current scan interval
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
