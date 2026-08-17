"""Coordinator for the EcoWater iQua backend.

This backend is used by the iQua app family (apioem.ecowater.com), which
covers devices such as the Aquahome Duo Smart as well as several other
rebranded EcoWater-platform softeners (Viessmann, North Star, Morton,
Whirlpool, Rheem, GE, Kenmore, ...).

Unlike the Hydrolink backend, iQua:
- Requires the device serial number to be entered by the user (there is no
  "list my devices" endpoint in general use).
- Reports its own volume unit per device instead of letting the user pick
  metric/imperial.
- Exposes a controllable water shutoff valve.
- Exposes far fewer historical/lifetime fields than Hydrolink (no lifetime
  totals, regeneration counters, dealer info, etc.).

The output of `_async_update_data` uses the same canonical dict keys as the
Hydrolink coordinator wherever the underlying data is equivalent, so the
`sensor` and `binary_sensor` platforms can stay backend-agnostic. Keys that
have no iQua equivalent are set to a neutral default (None/False).
"""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_DEVICE_SERIAL,
    IQUA_BASE_URL,
    IQUA_USER_AGENT,
    IQUA_VALVE_CLOSED,
    IQUA_VALVE_OPEN,
    SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL,
    UNIT_METRIC,
    UNIT_IMPERIAL,
    BACKEND_IQUA,
)
from .net import async_request_with_retry

_LOGGER = logging.getLogger(__name__)


class IquaCoordinator(DataUpdateCoordinator):
    """Coordinator for the iQua/OEM cloud API."""

    # Exposed for the switch/binary_sensor platforms to know this backend
    # supports valve control and a connectivity state.
    supports_valve_control = True

    def __init__(self, hass, entry):
        """Initialize the coordinator.

        Args:
            hass: HomeAssistant instance
            entry: ConfigEntry containing user configuration
        """
        self.entry = entry
        self.backend = BACKEND_IQUA
        self.device_serial = entry.data[CONF_DEVICE_SERIAL]
        self.language = hass.config.language[:2]

        # iQua reports its own unit per device; default until first update.
        self.unit_system = UNIT_METRIC

        interval = entry.options.get(
            SCAN_INTERVAL_MINUTES,
            entry.data.get(SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval)
        )

        self.session = async_get_clientsession(hass)
        self._token = None
        self._token_type = None
        self._token_expires = None
        _LOGGER.debug("IquaCoordinator initialized for serial %s", self.device_serial)

    def _headers(self, with_auth=True):
        """Build request headers, optionally including the bearer token."""
        headers = {"User-Agent": IQUA_USER_AGENT}
        if with_auth and self._token and self._token_type:
            headers["Authorization"] = f"{self._token_type} {self._token}"
        return headers

    async def _ensure_token(self):
        """Log in if we have no token yet, or it has expired."""
        if self._token is None or (
            self._token_expires is not None and dt_util.utcnow() > self._token_expires
        ):
            await self._login()

    async def _login(self):
        """Authenticate against the iQua API and store the bearer token."""
        payload = {
            "username": self.entry.data[CONF_USERNAME],
            "password": self.entry.data[CONF_PASSWORD],
        }
        try:
            response = await async_request_with_retry(
                self.session, "POST", f"{IQUA_BASE_URL}/auth/signin",
                json=payload, headers=self._headers(with_auth=False),
            )
        except Exception as ex:
            raise UpdateFailed(f"Could not reach EcoWater iQua login endpoint: {ex}") from ex

        if response.status == 401:
            raise UpdateFailed("Authentication failed for EcoWater iQua (check username/password)")
        response.raise_for_status()
        body = await response.json()
        if body.get("code") != "OK":
            raise UpdateFailed(f"iQua login error: {body.get('code')} ({body.get('message')})")

        data = body["data"]
        self._token = data["token"]
        self._token_type = data["tokenType"]
        self._token_expires = dt_util.utcnow() + timedelta(seconds=int(data["expiresIn"]))
        _LOGGER.debug("iQua token obtained, expires %s", self._token_expires)

    async def _request_json(self, method, path, **kwargs):
        """Perform an authenticated request, retrying once after a re-login on 401."""
        await self._ensure_token()
        url = f"{IQUA_BASE_URL}/{path}"
        response = await async_request_with_retry(
            self.session, method, url, headers=self._headers(), **kwargs
        )
        if response.status == 401:
            await self._login()
            response = await async_request_with_retry(
                self.session, method, url, headers=self._headers(), **kwargs
            )
        response.raise_for_status()
        body = await response.json()
        if body.get("code") != "OK":
            raise UpdateFailed(f"iQua request error: {body.get('code')} ({body.get('message')})")
        return body["data"]

    def _parse_device_data(self, data):
        """Map the raw iQua dashboard payload onto the integration's canonical data dict.

        Args:
            data: The "data" object from the /system/{serial}/dashboard response.

        Returns:
            dict: Mapped sensor data ready for use by sensor/binary_sensor/switch entities.
        """

        def raw(key, default=None):
            return data.get(key, {}).get("value", default)

        def as_int(key, default=None):
            value = raw(key)
            return int(value) if value is not None else default

        def as_float(key, default=None):
            value = raw(key)
            return float(value) if value is not None else default

        # 0 = gallons, 1 = liters
        volume_unit = as_int("volumeUnitEnum", 0)
        self.unit_system = UNIT_METRIC if volume_unit == 1 else UNIT_IMPERIAL

        salt_percent = data.get("saltLevelTenths", {}).get("percent")
        salt_tenths = raw("saltLevelTenths")

        return {
            "last_update": dt_util.now(),
            "model": f'{raw("modelDescription")} ({raw("modelId")})',
            "serial": self.device_serial,
            "connectivity": data.get("power") == "Online",

            "salt_level_percent": salt_percent,
            "salt_level_rounded": salt_percent,
            # Raw value is in tenths of a unit whose exact unit (lb/kg) has
            # not been confirmed against a real device - exposed as-is only.
            "salt_level_raw_tenths": salt_tenths,
            "out_of_salt_days": as_int("outOfSaltEstDays"),

            "water_used_today": as_int("gallonsUsedToday"),
            "calculated_daily_use": as_int("gallonsUsedToday"),
            "avg_daily_use": as_int("avgDailyUseGallons"),
            "water_available": as_int("totalWaterAvailGals"),
            "current_flow": as_float("currentWaterFlow"),
            "days_since_regen": as_int("daysSinceLastRegen"),
            "hardness": as_int("hardnessGrains"),

            "water_shutoff_valve_state": as_int("waterShutoffValveReq"),

            # Not exposed by the iQua dashboard endpoint.
            "low_salt_trip_days": None,
            "service_reminder": None,
            "total_water_used": None,
            "total_regens": None,
            "manual_regens": None,
            "avg_days_between_regens": None,
            "avg_salt_per_regen": None,
            "software_version": None,
            "rssi": None,
            "wifi_ssid": None,
            "days_in_operation": None,
            "power_outages": None,
            "dealer_name": None,
            "dealer_phone": None,
            "rock_removed_since_regen": None,
            "total_rock_removed": None,
            "total_salt_use": None,
            "water_used_in_last_regen": None,
            "is_regenerating": False,
            "salt_alert": False,
            "leak_alert": False,
            "error_alert": False,
            "alarm_beeping": False,
        }

    async def _async_update_data(self):
        """Periodically called by the base class to refresh data."""
        _LOGGER.debug("_async_update_data (iQua) STARTED at %s", dt_util.now())
        try:
            data = await self._request_json("GET", f"system/{self.device_serial}/dashboard")
            parsed = self._parse_device_data(data)
            _LOGGER.debug("_async_update_data (iQua) successful, data keys: %s", list(parsed.keys()))
            return parsed
        except UpdateFailed:
            raise
        except Exception as err:
            _LOGGER.exception("Error fetching EcoWater iQua data")
            raise UpdateFailed(f"Update failed: {err}")

    async def async_set_water_shutoff_valve(self, state: int):
        """Open or close the water shutoff valve.

        Args:
            state: IQUA_VALVE_OPEN (1) or IQUA_VALVE_CLOSED (0).
        """
        if state not in (IQUA_VALVE_CLOSED, IQUA_VALVE_OPEN):
            raise ValueError("Invalid water shutoff valve state (must be 0 or 1)")

        await self._ensure_token()
        url = f"{IQUA_BASE_URL}/system/{self.device_serial}/properties"
        payload = {"waterShutoffValve": state}

        response = await async_request_with_retry(
            self.session, "PUT", url, json=payload, headers=self._headers()
        )
        if response.status == 401:
            await self._login()
            response = await async_request_with_retry(
                self.session, "PUT", url, json=payload, headers=self._headers()
            )
        response.raise_for_status()
        body = await response.json()
        if body.get("code") != "OK":
            raise UpdateFailed(
                f"Failed to set water shutoff valve: {body.get('code')} ({body.get('message')})"
            )

        await self.async_request_refresh()
