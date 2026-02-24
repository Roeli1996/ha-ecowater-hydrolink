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
    LOGIN_URL,
    DATA_URL,
    HEADERS,
    CONF_USERNAME,
    CONF_PASSWORD,
    SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class EcowaterCoordinator(DataUpdateCoordinator):
    """Coördinator voor het periodiek ophalen van Ecowater data."""

    def __init__(self, hass, entry):
        """Initialiseer de coordinator met dynamisch interval."""
        self.entry = entry
        interval = entry.options.get(
            SCAN_INTERVAL_MINUTES,
            entry.data.get(SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL)
        )
        _LOGGER.debug("Coordinator update interval: %s minuten -> %s", interval, timedelta(minutes=interval))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval)
        )
        self.token = None
        self.session = async_get_clientsession(hass)
        _LOGGER.debug("Coordinator geïnitialiseerd")

    async def _async_request(self, method, url, **kwargs):
        """Voer een HTTP-request uit met retry bij DNS- en netwerkfouten."""
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                async with async_timeout.timeout(20):
                    return await self.session.request(method, url, **kwargs)
            except (ClientConnectorDNSError, ClientError, asyncio.TimeoutError) as err:
                if attempt < max_retries:
                    wait = 2 * (attempt + 1)
                    _LOGGER.warning(
                        "Fout bij %s %s (poging %d/%d): %s. Opnieuw proberen over %s seconden.",
                        method, url, attempt + 1, max_retries + 1, err, wait
                    )
                    await asyncio.sleep(wait)
                else:
                    _LOGGER.error("Max retries bereikt voor %s %s", method, url)
                    raise
            except Exception as err:
                _LOGGER.exception("Onverwachte fout bij %s %s", method, url)
                raise

    async def _get_token(self):
        """Haal een nieuw access token op."""
        auth_payload = {
            "email": self.entry.data[CONF_USERNAME],
            "password": self.entry.data[CONF_PASSWORD]
        }
        try:
            response = await self._async_request("POST", LOGIN_URL, json=auth_payload, headers=HEADERS)
            response.raise_for_status()
            data = await response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                _LOGGER.debug("Token succesvol opgehaald")
            else:
                _LOGGER.error("Geen token in response: %s", data)
            return token
        except Exception as ex:
            _LOGGER.exception("Authenticatie mislukt bij Ecowater")
            return None

    async def _fetch_data(self):
        """Intern ophalen van data."""
        # Zorg voor een geldig token
        if not self.token:
            self.token = await self._get_token()

        if not self.token:
            raise UpdateFailed("Kon niet inloggen bij Ecowater (geen token)")

        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = await self._async_request("GET", DATA_URL, headers=headers)
            _LOGGER.debug("Response status: %s", response.status)

            # Als token verlopen is (401), probeer één keer opnieuw met nieuw token
            if response.status == 401:
                _LOGGER.debug("Token verlopen, nieuw token aanvragen")
                self.token = await self._get_token()
                if not self.token:
                    raise UpdateFailed("Token vernieuwing mislukt")
                headers["Authorization"] = f"Bearer {self.token}"
                response = await self._async_request("GET", DATA_URL, headers=headers)
                _LOGGER.debug("Nieuwe response status: %s", response.status)

            response.raise_for_status()
            json_data = await response.json()
            _LOGGER.debug("JSON response ontvangen")

            devices = json_data.get("data", [])
            if not devices:
                raise UpdateFailed("Geen apparaten gevonden in Ecowater account")

            dev = devices[0]
            props = dev.get("properties", {})
            enriched = dev.get("enriched_data", {})
            wt = enriched.get("water_treatment", {})
            wts = wt.get("water_treatment_status", {})
            dealership = dev.get("dealership", {})

            # Hulpfunctie om veilig een waarde uit properties te halen
            def get_prop_value(key, subkey="value", default=None):
                prop = props.get(key, {})
                return prop.get(subkey, default)

            def get_prop_converted(key, default=None):
                prop = props.get(key, {})
                return prop.get("converted_value", default)

            # Data verzamelen
            data = {
                # Gebruik timezone-aware datetime voor timestamp device class
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
                "serial": dev.get("serial_number"),
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
            _LOGGER.debug("Data samengesteld: %s", {k: v for k, v in data.items() if k not in ["serial", "dealer_phone"]})
            return data

        except Exception as ex:
            _LOGGER.exception("Fout bij ophalen Ecowater data")
            raise UpdateFailed(f"Update mislukt: {ex}")

    async def _async_update_data(self):
        """Wordt periodiek aangeroepen door de basisklasse."""
        _LOGGER.debug("_async_update_data GESTART om %s", dt_util.now())
        try:
            data = await self._fetch_data()
            _LOGGER.debug("_async_update_data succesvol, data keys: %s", list(data.keys()))
            return data
        except Exception as err:
            _LOGGER.exception("Fout in _async_update_data")
            raise UpdateFailed(f"Update mislukt: {err}")