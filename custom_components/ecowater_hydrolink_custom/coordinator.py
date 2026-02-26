"""Coordinator for Ecowater Hydrolink Custom integration."""
import logging
import asyncio
from datetime import timedelta

import aiohttp
import async_timeout
from aiohttp.client_exceptions import ClientConnectorDNSError, ClientError

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    BASE_URLS,
    CONF_REGION,
    REGION_EU,
    CONF_USERNAME,
    CONF_PASSWORD,
    HEADERS,
    SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class EcowaterCoordinator(DataUpdateCoordinator):
    """Coordinator for periodically fetching Ecowater data."""

    def __init__(self, hass, entry):
        """Initialize the coordinator with dynamic interval and region."""
        self.entry = entry
        self.region = entry.data.get(CONF_REGION, REGION_EU)
        self.base_url = BASE_URLS[self.region]
        self.login_url = f"{self.base_url}/auth/login"
        self.devices_list_url = f"{self.base_url}/devices?all=false&per_page=200"
        self.device_id = None

        interval = entry.options.get(
            SCAN_INTERVAL_MINUTES,
            entry.data.get(SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL)
        )
        _LOGGER.debug(
            "Coordinator for region %s, update interval: %s minutes -> %s",
            self.region, interval, timedelta(minutes=interval)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval)
        )
        self.token = None
        self.session = async_get_clientsession(hass)
        _LOGGER.debug("Coordinator initialized")

    async def _async_request(self, method, url, **kwargs):
        """Perform an HTTP request with retry on DNS and network errors."""
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                async with async_timeout.timeout(20):
                    return await self.session.request(method, url, **kwargs)
            except (ClientConnectorDNSError, ClientError, asyncio.TimeoutError) as err:
                if attempt < max_retries:
                    wait = 2 * (attempt + 1)
                    _LOGGER.warning(
                        "Error on %s %s (attempt %d/%d): %s. Retrying in %s seconds.",
                        method, url, attempt + 1, max_retries + 1, err, wait
                    )
                    await asyncio.sleep(wait)
                else:
                    _LOGGER.error("Max retries reached for %s %s", method, url)
                    raise
            except Exception as err:
                _LOGGER.exception("Unexpected error on %s %s", method, url)
                raise

    async def _get_token(self):
        """Obtain a new access token."""
        auth_payload = {
            "email": self.entry.data[CONF_USERNAME],
            "password": self.entry.data[CONF_PASSWORD]
        }
        try:
            response = await self._async_request("POST", self.login_url, json=auth_payload, headers=HEADERS)
            response.raise_for_status()
            data = await response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                _LOGGER.debug("Token successfully obtained")
            else:
                _LOGGER.error("No token in response: %s", data)
            return token
        except Exception as ex:
            _LOGGER.exception("Authentication failed for Ecowater")
            return None

    async def _fetch_device_list(self, headers):
        """Fetch the list of devices to obtain the device ID."""
        response = await self._async_request("GET", self.devices_list_url, headers=headers)
        response.raise_for_status()
        json_data = await response.json()
        devices = json_data.get("data", [])
        if not devices:
            raise UpdateFailed("No devices found in Ecowater account")
        return devices[0]

    async def _parse_device_data(self, device):
        """Extract sensor data from a device object (from /devices endpoint)."""
        props = device.get("properties", {})
        enriched = device.get("enriched_data", {})
        wt = enriched.get("water_treatment", {})
        wts = wt.get("water_treatment_status", {})
        dealership = device.get("dealership", {})

        def get_prop_value(key, subkey="value", default=None):
            prop = props.get(key, {})
            return prop.get(subkey, default)

        def get_prop_converted(key, default=None):
            prop = props.get(key, {})
            return prop.get("converted_value", default)

        return {
            "last_update": dt_util.now(),
            "salt_level_percent": wt.get("salt_level_percent"),
            "salt_level_rounded": wt.get("salt_level", {}).get("salt_level_percent_rounded"),
            "out_of_salt_days": get_prop_value("out_of_salt_estimate_days"),
            "low_salt_trip_days": get_prop_value("low_salt_trip_level_days"),
            "service_reminder": wts.get("service_reminder_message"),
            "water_used_today": get_prop_converted("gallons_used_today"),
            "total_water_used": wt.get("total_water_used", {}).get("value"),
            "water_available": wt.get("treated_water_available", {}).get("value"),
            "current_flow": get_prop_converted("current_water_flow_gpm"),
            "avg_daily_use": get_prop_converted("avg_daily_use_gals"),
            "hardness": get_prop_value("hardness_grains"),
            "total_regens": get_prop_value("total_regens"),
            "manual_regens": get_prop_value("manual_regens"),
            "days_since_regen": wt.get("days_since_last_recharge") or get_prop_value("days_since_last_regen"),
            "avg_days_between_regens": get_prop_value("avg_days_between_regens"),
            "avg_salt_per_regen": get_prop_converted("avg_salt_per_regen_lbs"),
            "model": wt.get("model") or get_prop_value("model_description"),
            "serial": device.get("serial_number"),
            "software_version": get_prop_value("base_software_version"),
            "rssi": wt.get("rf_signal_strength_dbm"),
            "wifi_ssid": wt.get("wifi_ssid_name"),
            "days_in_operation": get_prop_value("days_in_operation"),
            "power_outages": get_prop_value("power_outage_count"),
            "dealer_name": dealership.get("name"),
            "dealer_phone": dealership.get("phone_number"),
            "is_regenerating": wt.get("regeneration_status") != "none" if wt.get("regeneration_status") else False,
            "salt_alert": wts.get("salt_level_alert", False),
            "leak_alert": wts.get("flow_monitor_alert", False),
            "error_alert": wts.get("error_code_alert", False),
        }

    async def _fetch_data(self):
        """Internal data fetching. Uses wake-up + detail if device ID known, else falls back to device list."""
        if not self.token:
            self.token = await self._get_token()

        if not self.token:
            raise UpdateFailed("Could not log in to Ecowater (no token)")

        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {self.token}"

        try:
            # If we don't have a device ID yet, fetch the device list and extract ID + data
            if self.device_id is None:
                device = await self._fetch_device_list(headers)
                self.device_id = device.get("id")
                _LOGGER.debug("Device ID obtained: %s", self.device_id)
                return await self._parse_device_data(device)

            # Device ID known: first send wake-up call to /live, then fetch fresh data from /detail-or-summary
            try:
                live_url = f"{self.base_url}/devices/{self.device_id}/live"
                await self._async_request("GET", live_url, headers=headers)
                _LOGGER.debug("Wake-up call sent to device %s", self.device_id)
            except Exception as wake_err:
                _LOGGER.warning("Wake-up call failed, continuing with data fetch: %s", wake_err)

            # Fetch current data from detail-or-summary
            detail_url = f"{self.base_url}/devices/{self.device_id}/detail-or-summary"
            response = await self._async_request("GET", detail_url, headers=headers)
            response.raise_for_status()
            json_data = await response.json()
            _LOGGER.debug("Detail data received for device %s", self.device_id)

            # Extract the device object from the response
            device = json_data.get("device")
            if not device:
                raise UpdateFailed("No device data found in detail response")

            return await self._parse_device_data(device)

        except Exception as ex:
            _LOGGER.exception("Error fetching Ecowater data")
            raise UpdateFailed(f"Update failed: {ex}")

    async def _async_update_data(self):
        """Periodically called by the base class."""
        _LOGGER.debug("_async_update_data STARTED at %s", dt_util.now())
        try:
            data = await self._fetch_data()
            _LOGGER.debug("_async_update_data successful, data keys: %s", list(data.keys()))
            return data
        except Exception as err:
            _LOGGER.exception("Error in _async_update_data")
            raise UpdateFailed(f"Update failed: {err}")
