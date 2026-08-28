"""Constants for the Ecowater Hydrolink Custom integration."""

DOMAIN = "ecowater_hydrolink_custom"
NAME = "Ecowater Hydrolink Custom"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Backend / cloud platform selection.
# HYDROLINK: app.hydrolinkhome.eu / .com - EcoWater "Hydrolink" app.
# IQUA: apioem.ecowater.com - EcoWater "iQua" app family, used by e.g.
#       Aquahome Duo Smart, Viessmann, North Star, Morton, Rheem, GE, Kenmore.
CONF_BACKEND = "backend"
BACKEND_HYDROLINK = "hydrolink"
BACKEND_IQUA = "iqua"
BACKEND_OPTIONS = {
    BACKEND_HYDROLINK: "EcoWater Hydrolink (Hydrolink app)",
    BACKEND_IQUA: "EcoWater iQua (iQua app, e.g. Aquahome Duo Smart)",
}

# Region selection (Hydrolink backend only)
CONF_REGION = "region"
REGION_EU = "EU"
REGION_US = "US"

# Unit system selection (Hydrolink backend only - iQua reports its own unit)
CONF_UNIT_SYSTEM = "unit_system"
UNIT_METRIC = "metric"
UNIT_IMPERIAL = "imperial"
UNIT_OPTIONS = {
    UNIT_METRIC: "Metric (liters, kg)",
    UNIT_IMPERIAL: "Imperial (gallons, lbs)",
}

# Base URLs per region (Hydrolink backend)
BASE_URLS = {
    REGION_EU: "https://api.hydrolinkhome.eu/v1",
    REGION_US: "https://api.hydrolinkhome.com/v1",
}

SCAN_INTERVAL_MINUTES = "scan_interval_minutes"
DEFAULT_SCAN_INTERVAL = 5

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/json",
    "Origin": "https://app.hydrolinkhome.eu",
    "Referer": "https://app.hydrolinkhome.eu/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

# iQua backend (Aquahome Duo Smart and other iQua-family softeners)
CONF_DEVICE_SERIAL = "device_serial_number"
IQUA_BASE_URL = "https://apioem.ecowater.com/v1"
# Mimics the official iQua Android app; the API has been observed to be
# strict about the User-Agent header.
IQUA_USER_AGENT = "okhttp/4.9.1"
# waterShutoffValveReq values reported by the iQua dashboard endpoint.
IQUA_VALVE_CLOSED = 0
IQUA_VALVE_OPEN = 1
IQUA_VALVE_NOT_PRESENT = 2

PLATFORMS = ["sensor", "binary_sensor", "switch"]
