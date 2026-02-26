"""Constants for the Ecowater Hydrolink Custom integration."""

DOMAIN = "ecowater_hydrolink_custom"
NAME = "Ecowater Hydrolink Custom"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Region selection
CONF_REGION = "region"
REGION_EU = "EU"
REGION_US = "US"

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

PLATFORMS = ["sensor", "binary_sensor"]
