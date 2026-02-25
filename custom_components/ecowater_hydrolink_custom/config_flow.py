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

class EcowaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecowater Hydrolink Custom."""

    VERSION = 2  # Increment version because we changed the data schema

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
