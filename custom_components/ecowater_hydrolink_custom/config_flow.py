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
    CONF_DEVICE_ID,
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


def _device_label(device):
    """Build a human-readable label for a device list entry.

    Uses the same field paths as EcowaterCoordinator._parse_device_data()
    so it stays consistent with what ends up in the "model" sensor.
    """
    serial = device.get("serial_number") or "?"
    water_treatment = device.get("enriched_data", {}).get("water_treatment", {}) or {}
    model = water_treatment.get("model")
    if not model:
        props = device.get("properties", {}) or {}
        model = props.get("model_description", {}).get("value")
    return f"{serial} ({model})" if model else serial


async def _login_and_fetch_devices(hass, region, username, password):
    """Log in and fetch the account's device list.

    Returns:
        (devices, error) tuple. On success, `devices` is a non-empty list
        of device dicts and `error` is None. On failure, `devices` is None
        and `error` is a code ("invalid_auth", "cannot_connect" or
        "no_devices") matching a key under config.error in strings.json.
    """
    session = async_get_clientsession(hass)
    base_url = BASE_URLS[region]
    headers = headers_for_region(region)

    try:
        async with async_timeout.timeout(20):
            login_response = await session.post(
                f"{base_url}/auth/login",
                json={"email": username, "password": password},
                headers=headers,
            )
    except (ClientConnectorDNSError, ClientError, asyncio.TimeoutError) as err:
        _LOGGER.warning("Could not reach Hydrolink API at %s: %s", base_url, err)
        return None, "cannot_connect"

    if login_response.status == 401:
        body = await login_response.text()
        _LOGGER.debug("Hydrolink login rejected (401) during setup: %s", body)
        return None, "invalid_auth"
    if login_response.status != 200:
        body = await login_response.text()
        _LOGGER.warning(
            "Unexpected status %s from Hydrolink login during setup: %s",
            login_response.status, body
        )
        return None, "cannot_connect"

    login_data = await login_response.json()
    token = login_data.get("access_token") or login_data.get("token")
    if not token:
        _LOGGER.warning("Hydrolink login returned 200 but no token during setup: %s", login_data)
        return None, "invalid_auth"

    try:
        async with async_timeout.timeout(20):
            devices_response = await session.get(
                f"{base_url}/devices?all=false&per_page=200",
                headers={**headers, "Authorization": f"Bearer {token}"},
            )
    except (ClientConnectorDNSError, ClientError, asyncio.TimeoutError) as err:
        _LOGGER.warning("Could not fetch Hydrolink device list: %s", err)
        return None, "cannot_connect"

    if devices_response.status != 200:
        body = await devices_response.text()
        _LOGGER.warning(
            "Unexpected status %s fetching Hydrolink device list during setup: %s",
            devices_response.status, body
        )
        return None, "cannot_connect"

    devices = (await devices_response.json()).get("data", [])
    if not devices:
        return None, "no_devices"

    return devices, None


class EcowaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecowater Hydrolink Custom."""

    VERSION = 2

    def __init__(self):
        """Initialize the config flow's transient state."""
        self._pending_data = None
        self._devices = None

    async def async_step_user(self, user_input=None):
        """Step called when the user adds the integration."""
        errors = {}

        if user_input is not None:
            devices, error = await _login_and_fetch_devices(
                self.hass,
                user_input[CONF_REGION],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            if error is None:
                self._pending_data = user_input
                self._devices = devices
                if len(devices) == 1:
                    return await self._async_create_for_device(devices[0])
                return await self.async_step_select_device()
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

    async def async_step_select_device(self, user_input=None):
        """For accounts with more than one device, let the user pick which one to add."""
        if user_input is not None:
            chosen_id = user_input[CONF_DEVICE_ID]
            device = next(d for d in self._devices if str(d.get("id")) == chosen_id)
            return await self._async_create_for_device(device)

        device_options = {
            str(device.get("id")): _device_label(device) for device in self._devices
        }
        data_schema = vol.Schema(
            {vol.Required(CONF_DEVICE_ID): vol.In(device_options)}
        )
        return self.async_show_form(step_id="select_device", data_schema=data_schema)

    async def _async_create_for_device(self, device):
        """Create the config entry for a specific device.

        Each device gets its own unique_id, so accounts with multiple
        devices can add the integration once per device instead of always
        ending up polling whichever device the API happens to list first.
        """
        device_id = device.get("id")
        await self.async_set_unique_id(str(device_id))
        self._abort_if_unique_id_configured()

        data = {**self._pending_data, CONF_DEVICE_ID: device_id}
        title = f"Ecowater Hydrolink Custom ({device.get('serial_number') or device_id})"
        return self.async_create_entry(title=title, data=data)

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
