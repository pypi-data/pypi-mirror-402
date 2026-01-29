"""API client for SMN Argentina weather service."""

from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timedelta, timezone
import json
import logging
import re
from typing import Any

import aiohttp

from .const import (
    API_ALERT_ENDPOINT,
    API_COORD_ENDPOINT,
    API_FORECAST_ENDPOINT,
    API_HEAT_WARNING_ENDPOINT,
    API_SHORTTERM_ALERT_ENDPOINT,
    API_WEATHER_ENDPOINT,
    DEFAULT_TIMEOUT,
    TOKEN_URL,
)
from .exceptions import (
    SMNAuthenticationError,
    SMNConnectionError,
    SMNTokenError,
)

_LOGGER = logging.getLogger(__name__)


class SMNTokenManager:
    """Manage JWT token for SMN API authentication."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the token manager.

        Args:
            session: aiohttp client session for making HTTP requests.
        """
        self._session = session
        self._token: str | None = None
        self._token_expiration: datetime | None = None

    def _decode_jwt_payload(self, token: str) -> dict[str, Any]:
        """Decode JWT payload without verification.

        Args:
            token: JWT token string.

        Returns:
            Decoded payload as dictionary.
        """
        try:
            # Split the JWT into parts
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")

            # Decode the payload (second part)
            # Add padding if needed
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception as err:
            _LOGGER.error("Error decoding JWT: %s", err)
            return {}

    async def fetch_token(self) -> str:
        """Fetch JWT token from SMN website.

        Returns:
            JWT token string.

        Raises:
            SMNTokenError: If token cannot be fetched or parsed.
            SMNConnectionError: If connection to SMN fails.
        """
        try:
            _LOGGER.debug("Fetching JWT token from %s", TOKEN_URL)
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await self._session.get(TOKEN_URL)
                response.raise_for_status()
                html = await response.text()

                _LOGGER.debug("Received HTML response, length: %d bytes", len(html))

                # Extract token from localStorage.setItem('token', 'eyJ...')
                # SMN always uses this exact format in a script tag
                pattern = (
                    r"localStorage\.setItem\(['\"]token['\"]\s*,\s*['\"]([^'\"]+)['\"]"
                )
                match = re.search(pattern, html)

                if not match:
                    # Log HTML snippet for debugging
                    lines = html.split("\n")
                    relevant_lines = [line for line in lines if "token" in line.lower()]
                    _LOGGER.error(
                        "Could not find token in HTML. Lines containing 'token' (%d found):",
                        len(relevant_lines),
                    )
                    for line in relevant_lines[:5]:  # Log first 5 matches
                        _LOGGER.error("  %s", line.strip()[:200])

                    raise SMNTokenError(
                        "Could not find token in HTML. Check logs for details"
                    )

                token = match.group(1)
                _LOGGER.info("Found token (length: %d)", len(token))

                # Validate token format (JWT should start with eyJ)
                if not token.startswith("eyJ"):
                    _LOGGER.warning(
                        "Token doesn't look like a JWT (doesn't start with 'eyJ'): %s",
                        token[:20],
                    )

                # Decode token to get expiration
                payload = self._decode_jwt_payload(token)
                if "exp" in payload:
                    self._token_expiration = datetime.fromtimestamp(
                        payload["exp"], tz=timezone.utc
                    )
                    _LOGGER.info(
                        "Token expires at: %s", self._token_expiration.isoformat()
                    )
                else:
                    _LOGGER.warning("Token does not contain expiration field")

                self._token = token
                return token

        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP error fetching token from %s: %s", TOKEN_URL, err)
            raise SMNConnectionError(f"Error fetching token: {err}") from err
        except SMNTokenError:
            raise
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching token")
            raise SMNTokenError(f"Unexpected error fetching token: {err}") from err

    async def get_token(self) -> str:
        """Get valid token, refreshing if necessary.

        Returns:
            Valid JWT token string.

        Raises:
            SMNTokenError: If token cannot be obtained.
        """
        # Check if we have a token and it's still valid
        if self._token and self._token_expiration:
            # Refresh if token expires in less than 5 minutes
            now = datetime.now(tz=timezone.utc)
            if now < (self._token_expiration - timedelta(minutes=5)):
                return self._token

        # Fetch new token
        return await self.fetch_token()

    @property
    def token_expiration(self) -> datetime | None:
        """Return token expiration time."""
        return self._token_expiration


class SMNApiClient:
    """API client for SMN Argentina weather service."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token_manager: SMNTokenManager | None = None,
    ) -> None:
        """Initialize the API client.

        Args:
            session: aiohttp client session for making HTTP requests.
            token_manager: Optional token manager instance. If not provided,
                          a new one will be created.
        """
        self._session = session
        self._token_manager = token_manager or SMNTokenManager(session)

    @property
    def token_manager(self) -> SMNTokenManager:
        """Return the token manager instance."""
        return self._token_manager

    async def _get_headers(self) -> dict[str, str]:
        """Get headers with authentication token.

        Returns:
            Headers dictionary with Authorization token.

        Raises:
            SMNAuthenticationError: If token cannot be obtained.
        """
        try:
            token = await self._token_manager.get_token()
            _LOGGER.debug(
                "Using token for API request (first 20 chars): %s", token[:20]
            )
        except Exception as err:
            _LOGGER.error("Failed to get authentication token: %s", err)
            raise SMNAuthenticationError(
                f"Failed to get authentication token: {err}"
            ) from err
        return {
            "Authorization": f"JWT {token}",
            "Accept": "application/json",
        }

    async def async_get_location(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Get location ID from coordinates.

        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.

        Returns:
            Location data dictionary.

        Raises:
            SMNConnectionError: If API request fails.
            SMNAuthenticationError: If authentication fails.
        """
        url = f"{API_COORD_ENDPOINT}?lat={latitude}&lon={longitude}"
        headers = await self._get_headers()

        try:
            _LOGGER.debug("Fetching location ID from: %s", url)
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await self._session.get(url, headers=headers)

                if response.status == 401:
                    response_text = await response.text()
                    _LOGGER.error(
                        "401 Unauthorized when fetching location ID. Response: %s",
                        response_text[:200],
                    )
                    raise SMNAuthenticationError("Unauthorized access to SMN API")

                response.raise_for_status()
                data = await response.json()

                _LOGGER.debug("Location API response: %s", data)
                return data

        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP error fetching location ID: %s", err)
            raise SMNConnectionError(f"Error fetching location ID: {err}") from err
        except SMNAuthenticationError:
            raise
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching location ID")
            raise SMNConnectionError(
                f"Unexpected error fetching location ID: {err}"
            ) from err

    async def async_get_current_weather(self, location_id: str) -> dict[str, Any]:
        """Fetch current weather data.

        Args:
            location_id: SMN location identifier.

        Returns:
            Current weather data dictionary.

        Raises:
            SMNConnectionError: If API request fails.
        """
        url = f"{API_WEATHER_ENDPOINT}/{location_id}"
        headers = await self._get_headers()

        try:
            _LOGGER.debug("Fetching current weather from: %s", url)
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await self._session.get(url, headers=headers)
                response.raise_for_status()
                data = await response.json()

                _LOGGER.debug("Current weather response: %s", data)
                return data

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching current weather: %s", err)
            raise SMNConnectionError(f"Error fetching current weather: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching current weather")
            raise SMNConnectionError(
                f"Unexpected error fetching current weather: {err}"
            ) from err

    async def async_get_forecast(self, location_id: str) -> dict[str, Any]:
        """Fetch forecast data.

        Args:
            location_id: SMN location identifier.

        Returns:
            Forecast data dictionary.

        Raises:
            SMNConnectionError: If API request fails.
        """
        url = f"{API_FORECAST_ENDPOINT}/{location_id}"
        headers = await self._get_headers()

        try:
            _LOGGER.debug("Fetching forecast from: %s", url)
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await self._session.get(url, headers=headers)
                response.raise_for_status()
                data = await response.json()

                _LOGGER.debug("Forecast response: %s", data)
                return data

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching forecast: %s", err)
            raise SMNConnectionError(f"Error fetching forecast: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching forecast")
            raise SMNConnectionError(
                f"Unexpected error fetching forecast: {err}"
            ) from err

    async def async_get_alerts(self, location_id: str) -> dict[str, Any]:
        """Fetch weather alerts.

        Args:
            location_id: SMN location identifier.

        Returns:
            Alerts data dictionary. Returns empty dict if no alerts or on error.
        """
        url = f"{API_ALERT_ENDPOINT}/{location_id}"
        headers = await self._get_headers()

        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await self._session.get(url, headers=headers)
                response.raise_for_status()
                data = await response.json()

                _LOGGER.debug(
                    "Fetched alerts for location %s: %d warnings",
                    location_id,
                    len(data.get("warnings", [])) if isinstance(data, dict) else 0,
                )
                return data if isinstance(data, dict) else {}

        except aiohttp.ClientError as err:
            _LOGGER.debug("Error fetching alerts (may be normal if none): %s", err)
            return {}
        except Exception:
            _LOGGER.exception("Unexpected error fetching alerts")
            return {}

    async def async_get_shortterm_alerts(
        self, location_id: str
    ) -> list[dict[str, Any]]:
        """Fetch short-term severe weather alerts.

        Args:
            location_id: SMN location identifier.

        Returns:
            List of short-term alert dictionaries. Returns empty list on error.
        """
        url = f"{API_SHORTTERM_ALERT_ENDPOINT}/{location_id}"
        headers = await self._get_headers()

        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await self._session.get(url, headers=headers)
                response.raise_for_status()
                data = await response.json()

                _LOGGER.debug(
                    "Fetched %d short-term alerts for location %s",
                    len(data) if isinstance(data, list) else 0,
                    location_id,
                )
                return data if isinstance(data, list) else []

        except aiohttp.ClientError as err:
            _LOGGER.debug(
                "Error fetching short-term alerts (may be normal if none): %s", err
            )
            return []
        except Exception:
            _LOGGER.exception("Unexpected error fetching short-term alerts")
            return []

    async def async_get_heat_warnings(self, area_id: str) -> dict[str, Any]:
        """Fetch heat warnings.

        Args:
            area_id: SMN area identifier.

        Returns:
            Heat warnings data dictionary. Returns empty dict on error.
        """
        url = f"{API_HEAT_WARNING_ENDPOINT}/{area_id}"
        headers = await self._get_headers()

        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await self._session.get(url, headers=headers)
                response.raise_for_status()
                data = await response.json()

                _LOGGER.debug(
                    "Fetched heat warning for area %s: level=%s",
                    area_id,
                    data.get("level") if isinstance(data, dict) else None,
                )
                return data if isinstance(data, dict) else {}

        except aiohttp.ClientError as err:
            _LOGGER.debug(
                "Error fetching heat warnings (may be normal if none): %s", err
            )
            return {}
        except Exception:
            _LOGGER.exception("Unexpected error fetching heat warnings")
            return {}
