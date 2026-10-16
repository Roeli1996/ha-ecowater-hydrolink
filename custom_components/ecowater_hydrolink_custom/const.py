"""Constants for the Ecowater Hydrolink Custom integration."""

DOMAIN = "ecowater_hydrolink_custom"
NAME = "Ecowater Hydrolink Custom"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Explicit device selection (for accounts with more than one Hydrolink
# device). Older config entries created before this existed simply omit
# this key, and the coordinator falls back to auto-selecting the first
# device the account's device list returns - unchanged legacy behavior.
CONF_DEVICE_ID = "device_id"

# Region selection.
# EU / US are the two Hydrolink servers. IQUA / IQUA2 are the servers of the
# EcoWater "iQua" and "iQua 2" apps, which run the same platform (identical
# routes and device data model) under other hostnames - this is what devices
# such as the Aquahome Duo Smart (Viessmann) are connected to.
CONF_REGION = "region"
REGION_EU = "EU"
REGION_US = "US"
REGION_IQUA = "IQUA"
REGION_IQUA2 = "IQUA2"
IQUA_REGIONS = (REGION_IQUA, REGION_IQUA2)

# Labels shown in the setup form.
REGION_OPTIONS = {
    REGION_EU: "Hydrolink Europe (app.hydrolinkhome.eu)",
    REGION_US: "Hydrolink US / Other (app.hydrolinkhome.com)",
    REGION_IQUA2: "iQua 2 (app.iqua2.com) - e.g. Aquahome Duo Smart",
    REGION_IQUA: "iQua (iQua app) - older iQua accounts",
}

# Unit system selection
CONF_UNIT_SYSTEM = "unit_system"
UNIT_METRIC = "metric"
UNIT_IMPERIAL = "imperial"
UNIT_OPTIONS = {
    UNIT_METRIC: "Metric (liters, kg)",
    UNIT_IMPERIAL: "Imperial (gallons, lbs)",
}

# Base URLs per region
BASE_URLS = {
    REGION_EU: "https://api.hydrolinkhome.eu/v1",
    REGION_US: "https://api.hydrolinkhome.com/v1",
    REGION_IQUA: "https://api.myiquaapp.com/v1",
    REGION_IQUA2: "https://api.iqua2.com/v1",
}

SCAN_INTERVAL_MINUTES = "scan_interval_minutes"
DEFAULT_SCAN_INTERVAL = 5

# Web app origins per region (used for the Origin/Referer headers below).
APP_URLS = {
    REGION_EU: "https://app.hydrolinkhome.eu",
    REGION_US: "https://app.hydrolinkhome.com",
}

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}


def headers_for_region(region):
    """Build request headers for the selected region.

    Hydrolink: browser-style headers with Origin/Referer matching the region
    (previously hardcoded to the EU app URL for every region).

    iQua / iQua 2: plain JSON headers only. The community clients that are
    known to work against these servers send no browser User-Agent and no
    Origin/Referer, so we don't pretend to be a browser there.
    """
    if region in IQUA_REGIONS:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    app_url = APP_URLS.get(region, APP_URLS[REGION_EU])
    return {
        **HEADERS,
        "Origin": app_url,
        "Referer": f"{app_url}/",
    }


def devices_list_url(region):
    """Return the URL that lists the devices of the logged-in account."""
    base = BASE_URLS[region]
    if region in IQUA_REGIONS:
        # The iQua clients call the plain endpoint; the query string is a
        # Hydrolink web-app detail we have no evidence the iQua servers need.
        return f"{base}/devices"
    return f"{base}/devices?all=false&per_page=200"


PLATFORMS = ["sensor", "binary_sensor"]
