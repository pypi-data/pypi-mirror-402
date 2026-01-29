"""SMN Argentina API client library.

Async Python client for the Servicio Meteorológico Nacional Argentina (SMN) API.
Provides weather data, forecasts, and alerts for locations in Argentina.
"""

from .client import SMNApiClient, SMNTokenManager
from .exceptions import (
    SMNAuthenticationError,
    SMNConnectionError,
    SMNError,
    SMNTokenError,
)

__all__ = [
    "SMNApiClient",
    "SMNTokenManager",
    "SMNError",
    "SMNConnectionError",
    "SMNAuthenticationError",
    "SMNTokenError",
]

__version__ = "1.0.0"
