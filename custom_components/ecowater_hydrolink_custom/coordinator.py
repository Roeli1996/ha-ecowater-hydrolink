"""Coordinator for Ecowater Hydrolink Custom integration.

This module handles all API communication, data fetching, and periodic updates.
It acts as the central data hub for the integration.
"""

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
    CONF_UNIT_SYSTEM,
    UNIT_METRIC,
    HEADERS,
    SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class EcowaterCoordinator(DataUpdateCoordinator):
    """Coordinator for periodically fetching Ecowater data.

    This class extends DataUpdateCoordinator and handles:
    - Authentication and token renewal
    - Device ID discovery
    - Wake‑up calls to /live endpoint
    - Data retrieval from /detail-or-summary
    - Unit system and language awareness
    - Calculation of daily usage from total water used
    """

    def __init__(self, hass, entry):
        """Initialize the coordinator.

        Args:
            hass: HomeAssistant instance
            entry: ConfigEntry containing user configuration
        """
        self.entry = entry

        # Region selection (default to EU if not set)
        self.region = entry.data.get(CONF_REGION, REGION_EU)

        # Unit system (metric/imperial) – taken from options, falling back to data
        self.unit_system = entry.options.get(
            CONF_UNIT_SYSTEM, entry.data.get(CONF_UNIT_SYSTEM, UNIT_METRIC)
        )

        # Store the Home Assistant language (first two letters) for unit translations
        # This allows sensors to display e.g. "days" in English, "dagen" in Dutch, etc.
        self.language = hass.config.language[:2]

        _LOGGER.debug(
            "Coordinator unit_system = %s, language = %s (from options: %s, from data: %s)",
            self.unit_system,
            self.language,
            entry.options.get(CONF_UNIT_SYSTEM),
            entry.data.get(CONF_UNIT_SYSTEM),
        )

        # Construct API endpoints based on selected region
        self.base_url = BASE_URLS[self.region]
        self.login_url = f"{self.base_url}/auth/login"
        self.devices_list_url = f"{self.base_url}/devices?all=false&per_page=200"
        self.device_id = None  # Will be filled after first device list fetch

        # Variables for calculated daily usage (derived from total_water_used)
        self._previous_total = None   # Last known total water value
        self._daily_total = 0.0       # Accumulated usage since midnight
        self._last_date = None         # Date of the last update (used for reset)

        # Update interval (in minutes) – from options, falling back to data
        interval = entry.options.get(
            SCAN_INTERVAL_MINUTES,
            entry.data.get(SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL)
        )
        _LOGGER.debug(
            "Coordinator for region %s, unit system %s, update interval: %s minutes -> %s",
            self.region, self.unit_system, interval, timedelta(minutes=interval)
        )

        # Initialize the base DataUpdateCoordinator
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
        """Perform an HTTP request with automatic retries on DNS/network errors.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            **kwargs: Additional arguments for aiohttp request

        Returns:
            aiohttp.ClientResponse on success

        Raises:
            Exception if all retries fail
        """
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
        """Obtain a new access token from the login endpoint.

        Returns:
            str: Access token, or None if authentication failed.
        """
        auth_payload = {
            "email": self.entry.data[CONF_USERNAME],
            "password": self.entry.data[CONF_PASSWORD]
        }
        try:
            response = await self._async_request(
                "POST", self.login_url, json=auth_payload, headers=HEADERS
            )
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
        """Fetch the list of devices to obtain the device ID.

        Args:
            headers: Request headers including Authorization

        Returns:
            dict: The first device object from the list.

        Raises:
            UpdateFailed if no devices found.
        """
        response = await self._async_request(
            "GET", self.devices_list_url, headers=headers
        )
        response.raise_for_status()
        json_data = await response.json()
        devices = json_data.get("data", [])
        if not devices:
            raise UpdateFailed("No devices found in Ecowater account")
        return devices[0]

    async def _parse_device_data(self, device):
        """Extract sensor data from a device object.

        This method processes the raw device JSON (from either /devices or /detail-or-summary)
        and builds a dictionary of sensor values.

        Args:
            device: Device object as returned by the API

        Returns:
            dict: Mapped sensor data ready for use by sensor entities.
        """
        props = device.get("properties", {})
        enriched = device.get("enriched_data", {})
        wt = enriched.get("water_treatment", {})
        wts = wt.get("water_treatment_status", {})
        dealership = device.get("dealership", {})

        # Helper to safely extract a property value (e.g., "value" field)
        def get_prop_value(key, subkey="value", default=None):
            prop = props.get(key, {})
            return prop.get(subkey, default)

        # Helper to safely extract the converted (metric) value
        def get_prop_converted(key, default=None):
            prop = props.get(key, {})
            return prop.get("converted_value", default)

        # Helper to get the appropriate measurement based on the selected unit system
        def get_measurement(prop_key, default=None):
            if self.unit_system == UNIT_METRIC:
                return get_prop_converted(prop_key, default)
            else:
                return get_prop_value(prop_key, "value", default)

        # Optional debug logging for key sensors
        test_keys = [
            "gallons_used_today", "total_outlet_water_gals", "treated_water_avail_gals",
            "current_water_flow_gpm", "avg_salt_per_regen_lbs"
        ]
        for key in test_keys:
            metric_val = get_prop_converted(key)
            imperial_val = get_prop_value(key)
            chosen_val = get_measurement(key)
            _LOGGER.debug(
                "Key %s: metric=%s, imperial=%s, chosen=%s",
                key, metric_val, imperial_val, chosen_val
            )

        # Build the main data dictionary
        data = {
            "last_update": dt_util.now(),
            "salt_level_percent": wt.get("salt_level_percent"),
            "salt_level_rounded": wt.get("salt_level", {}).get("salt_level_percent_rounded"),
            "out_of_salt_days": get_prop_value("out_of_salt_estimate_days"),
            "low_salt_trip_days": get_prop_value("low_salt_trip_level_days"),
            "service_reminder": wts.get("service_reminder_message"),

            # Unit‑dependent fields (metric/imperial)
            "water_used_today": get_measurement("gallons_used_today"),
            "total_water_used": get_measurement("total_outlet_water_gals"),
            "water_available": get_measurement("treated_water_avail_gals"),
            "current_flow": get_measurement("current_water_flow_gpm"),
            "avg_daily_use": get_measurement("avg_daily_use_gals"),
            "avg_salt_per_regen": get_measurement("avg_salt_per_regen_lbs"),

            # Other fields (not unit‑sensitive)
            "hardness": get_prop_value("hardness_grains"),
            "total_regens": get_prop_value("total_regens"),
            "manual_regens": get_prop_value("manual_regens"),
            "days_since_regen": wt.get("days_since_last_recharge") or get_prop_value("days_since_last_regen"),
            "avg_days_between_regens": get_prop_value("avg_days_between_regens"),
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
            "alarm_beeping": get_prop_value("alarm_is_beeping", default=False),
        }

        # Rock removed since last regeneration – store both metric and imperial values
        rock_metric = get_prop_converted("rock_removed_since_rech_lbs")
        rock_imperial = get_prop_value("rock_removed_since_rech_lbs")
        data["rock_removed_since_regen"] = rock_metric if self.unit_system == UNIT_METRIC else rock_imperial
        data["rock_removed_since_regen_metric"] = rock_metric
        data["rock_removed_since_regen_imperial"] = rock_imperial

        # Total rock removed – both metric and imperial
        total_rock_metric = get_prop_converted("total_rock_removed_lbs")
        total_rock_imperial = get_prop_value("total_rock_removed_lbs")
        data["total_rock_removed"] = total_rock_metric if self.unit_system == UNIT_METRIC else total_rock_imperial
        data["total_rock_removed_metric"] = total_rock_metric
        data["total_rock_removed_imperial"] = total_rock_imperial

        # Total salt used – both metric and imperial
        total_salt_metric = get_prop_converted("total_salt_use_lbs")
        total_salt_imperial = get_prop_value("total_salt_use_lbs")
        data["total_salt_use"] = total_salt_metric if self.unit_system == UNIT_METRIC else total_salt_imperial
        data["total_salt_use_metric"] = total_salt_metric
        data["total_salt_use_imperial"] = total_salt_imperial

        # ----- Calculated daily usage -----
        # This is an alternative to the sometimes delayed "water_used_today" from the cloud.
        # It accumulates the difference of total_water_used between updates and resets at midnight.
        current_total = data.get("total_water_used")
        if current_total is not None:
            now = dt_util.now()
            # Reset at midnight
            if self._last_date is None:
                self._last_date = now.date()
                self._daily_total = 0.0
            elif self._last_date != now.date():
                self._daily_total = 0.0
                self._last_date = now.date()

            # If we have a previous total, compute the delta and add to daily total
            if self._previous_total is not None:
                delta = current_total - self._previous_total
                # Ignore negative delta (could happen if counter resets)
                if delta > 0:
                    self._daily_total += delta
                elif delta < 0:
                    _LOGGER.warning(
                        "Negative delta detected: previous_total=%s, current_total=%s",
                        self._previous_total, current_total
                    )
            # Store current total for next time
            self._previous_total = current_total

            data["calculated_daily_use"] = self._daily_total
        else:
            data["calculated_daily_use"] = 0

        _LOGGER.debug("Data assembled (unit system: %s)", self.unit_system)
        return data

    async def _fetch_data(self):
        """Internal data fetching routine.

        If device ID is unknown, it first fetches the device list to obtain it.
        Otherwise, it sends a wake‑up call to /live and then retrieves fresh data
        from /detail-or-summary.

        Returns:
            dict: Sensor data from _parse_device_data.

        Raises:
            UpdateFailed on critical errors.
        """
        if not self.token:
            self.token = await self._get_token()

        if not self.token:
            raise UpdateFailed("Could not log in to Ecowater (no token)")

        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {self.token}"

        try:
            if self.device_id is None:
                # First run: fetch device list to get the ID
                device = await self._fetch_device_list(headers)
                self.device_id = device.get("id")
                _LOGGER.debug("Device ID obtained: %s", self.device_id)
                return await self._parse_device_data(device)

            # Normal scheduled update: wake up the device via /live, then fetch details
            try:
                live_url = f"{self.base_url}/devices/{self.device_id}/live"
                await self._async_request("GET", live_url, headers=headers)
                _LOGGER.debug("Wake-up call sent to device %s", self.device_id)
            except Exception as wake_err:
                _LOGGER.warning(
                    "Wake-up call failed, continuing with data fetch: %s", wake_err
                )

            detail_url = f"{self.base_url}/devices/{self.device_id}/detail-or-summary"
            response = await self._async_request("GET", detail_url, headers=headers)
            response.raise_for_status()
            json_data = await response.json()
            _LOGGER.debug("Detail data received for device %s", self.device_id)

            device = json_data.get("device")
            if not device:
                raise UpdateFailed("No device data found in detail response")

            return await self._parse_device_data(device)

        except Exception as ex:
            _LOGGER.exception("Error fetching Ecowater data")
            raise UpdateFailed(f"Update failed: {ex}")

    async def _async_update_data(self):
        """Periodically called by the base class to refresh data.

        Returns:
            dict: The latest sensor data.
        """
        _LOGGER.debug("_async_update_data STARTED at %s", dt_util.now())
        try:
            data = await self._fetch_data()
            _LOGGER.debug(
                "_async_update_data successful, data keys: %s", list(data.keys())
            )
            return data
        except Exception as err:
            _LOGGER.exception("Error in _async_update_data")
            raise UpdateFailed(f"Update failed: {err}")
