"""Config flow for Ecowater Hydrolink Custom integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_BACKEND,
    BACKEND_HYDROLINK,
    BACKEND_IQUA,
    BACKEND_OPTIONS,
    CONF_REGION,
    REGION_EU,
    REGION_US,
    CONF_UNIT_SYSTEM,
    UNIT_METRIC,
    UNIT_OPTIONS,
    CONF_DEVICE_SERIAL,
    SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class EcowaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecowater Hydrolink Custom."""

    VERSION = 3

    async def async_step_user(self, user_input=None):
        """First step: choose which EcoWater cloud backend/app the device uses."""
        if user_input is not None:
            if user_input[CONF_BACKEND] == BACKEND_IQUA:
                return await self.async_step_iqua()
            return await self.async_step_hydrolink()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_BACKEND, default=BACKEND_HYDROLINK): vol.In(BACKEND_OPTIONS),
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_hydrolink(self, user_input=None):
        """Step for the Hydrolink backend (Hydrolink app)."""
        errors = {}

        if user_input is not None:
            data = {**user_input, CONF_BACKEND: BACKEND_HYDROLINK}
            return self.async_create_entry(
                title="Ecowater Hydrolink Custom",
                data=data
            )

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
                vol.Required(CONF_UNIT_SYSTEM, default=UNIT_METRIC): vol.In(UNIT_OPTIONS),
                vol.Optional(
                    SCAN_INTERVAL_MINUTES, default=DEFAULT_SCAN_INTERVAL
                ): int,
            }
        )

        return self.async_show_form(
            step_id="hydrolink",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_iqua(self, user_input=None):
        """Step for the iQua backend (iQua app, e.g. Aquahome Duo Smart)."""
        errors = {}

        if user_input is not None:
            data = {**user_input, CONF_BACKEND: BACKEND_IQUA}
            return self.async_create_entry(
                title=f"Ecowater iQua {user_input[CONF_DEVICE_SERIAL]}",
                data=data
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_DEVICE_SERIAL): str,
                vol.Optional(
                    SCAN_INTERVAL_MINUTES, default=DEFAULT_SCAN_INTERVAL
                ): int,
            }
        )

        return self.async_show_form(
            step_id="iqua",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EcowaterOptionsFlowHandler(config_entry)

    async def async_migrate_entry(self, hass, config_entry):
        """Migrate old entries."""
        _LOGGER.debug("Migrating from version %s", config_entry.version)

        if config_entry.version == 1:
            new_data = {**config_entry.data, CONF_REGION: REGION_EU}
            config_entry.version = 2
            hass.config_entries.async_update_entry(config_entry, data=new_data)
            _LOGGER.debug("Migration to version 2 complete")

        if config_entry.version == 2:
            new_data = {**config_entry.data, CONF_BACKEND: BACKEND_HYDROLINK}
            config_entry.version = 3
            hass.config_entries.async_update_entry(config_entry, data=new_data)
            _LOGGER.debug("Migration to version 3 complete")

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

        backend = self.config_entry.data.get(CONF_BACKEND, BACKEND_HYDROLINK)

        current_interval = self.config_entry.options.get(
            SCAN_INTERVAL_MINUTES,
            self.config_entry.data.get(SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL)
        )

        schema_dict = {}

        # Unit system is only user-selectable on Hydrolink; iQua reports its
        # own unit per device.
        if backend == BACKEND_HYDROLINK:
            current_unit = self.config_entry.options.get(
                CONF_UNIT_SYSTEM,
                self.config_entry.data.get(CONF_UNIT_SYSTEM, UNIT_METRIC)
            )
            schema_dict[vol.Required(CONF_UNIT_SYSTEM, default=current_unit)] = vol.In(UNIT_OPTIONS)

        schema_dict[vol.Optional(SCAN_INTERVAL_MINUTES, default=current_interval)] = int

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )
