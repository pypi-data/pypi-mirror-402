"""Constants for SMN Argentina API."""

from typing import Final

# API Endpoints
API_BASE_URL: Final = "https://ws1.smn.gob.ar/v1"
API_COORD_ENDPOINT: Final = f"{API_BASE_URL}/georef/location/coord"
API_FORECAST_ENDPOINT: Final = f"{API_BASE_URL}/forecast/location"
API_WEATHER_ENDPOINT: Final = f"{API_BASE_URL}/weather/location"
API_ALERT_ENDPOINT: Final = f"{API_BASE_URL}/warning/alert/location"
API_SHORTTERM_ALERT_ENDPOINT: Final = f"{API_BASE_URL}/warning/shortterm/location"
API_HEAT_WARNING_ENDPOINT: Final = f"{API_BASE_URL}/warning/heat/area"

# Token endpoint
TOKEN_URL: Final = "https://ws2.smn.gob.ar/"

# Default timeout for API requests (seconds)
DEFAULT_TIMEOUT: Final = 10
