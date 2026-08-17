"""Config flow for Ecowater Hydrolink Custom integration."""
import asyncio
import logging

import async_timeout
import voluptuous as vol
from aiohttp.client_exceptions import ClientConnectorDNSError, ClientError
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_REGION,
    REGION_EU,
    REGION_US,
    CONF_UNIT_SYSTEM,
    UNIT_METRIC,
    UNIT_OPTIONS,
    SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL,
    BASE_URLS,
    headers_for_region,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_login(hass, region, username, password):
    """Attempt an actual login against the Hydrolink API to verify credentials.

    Returns:
        None if the credentials are valid, otherwise an error code
        ("invalid_auth" or "cannot_connect") matching a key under
        config.error in strings.json.
    """
    session = async_get_clientsession(hass)
    login_url = f"{BASE_URLS[region]}/auth/login"
    payload = {"email": username, "password": password}

    try:
        async with async_timeout.timeout(20):
            response = await session.post(
                login_url, json=payload, headers=headers_for_region(region)
            )
    except (ClientConnectorDNSError, ClientError, asyncio.TimeoutError) as err:
        _LOGGER.warning("Could not reach Hydrolink API at %s: %s", login_url, err)
        return "cannot_connect"

    if response.status == 401:
        body = await response.text()
        _LOGGER.debug("Hydrolink login rejected (401) during setup: %s", body)
        return "invalid_auth"
    if response.status != 200:
        body = await response.text()
        _LOGGER.warning(
            "Unexpected status %s from Hydrolink login during setup: %s",
            response.status, body
        )
        return "cannot_connect"

    data = await response.json()
    if not (data.get("access_token") or data.get("token")):
        _LOGGER.warning("Hydrolink login returned 200 but no token during setup: %s", data)
        return "invalid_auth"

    return None


class EcowaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecowater Hydrolink Custom."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Step called when the user adds the integration."""
        errors = {}

        if user_input is not None:
            error = await _validate_login(
                self.hass,
                user_input[CONF_REGION],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            if error is None:
                return self.async_create_entry(
                    title="Ecowater Hydrolink Custom",
                    data=user_input
                )
            errors["base"] = error

        # Re-populate defaults from the previous attempt so a retry after a
        # validation error doesn't force the user to redo their selections.
        user_input = user_input or {}
        username_field = (
            vol.Required(CONF_USERNAME, default=user_input[CONF_USERNAME])
            if CONF_USERNAME in user_input
            else vol.Required(CONF_USERNAME)
        )
        data_schema = vol.Schema(
            {
                username_field: str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_REGION, default=user_input.get(CONF_REGION, REGION_EU)): vol.In(
                    {
                        REGION_EU: "Europe (app.hydrolinkhome.eu)",
                        REGION_US: "US / Other (app.hydrolinkhome.com)",
                    }
                ),
                vol.Required(
                    CONF_UNIT_SYSTEM, default=user_input.get(CONF_UNIT_SYSTEM, UNIT_METRIC)
                ): vol.In(UNIT_OPTIONS),
                vol.Optional(
                    SCAN_INTERVAL_MINUTES,
                    default=user_input.get(SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL)
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
        return EcowaterOptionsFlowHandler(config_entry)

    async def async_migrate_entry(self, hass, config_entry):
        """Migrate old entry."""
        _LOGGER.debug("Migrating from version %s", config_entry.version)
        if config_entry.version == 1:
            new_data = {**config_entry.data, CONF_REGION: REGION_EU}
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

        # Determine current values
        current_unit = self.config_entry.options.get(
            CONF_UNIT_SYSTEM,
            self.config_entry.data.get(CONF_UNIT_SYSTEM, UNIT_METRIC)
        )
        current_interval = self.config_entry.options.get(
            SCAN_INTERVAL_MINUTES,
            self.config_entry.data.get(SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL)
        )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_UNIT_SYSTEM, default=current_unit): vol.In(UNIT_OPTIONS),
                vol.Optional(SCAN_INTERVAL_MINUTES, default=current_interval): int,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
