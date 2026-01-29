"""Exceptions for SMN Argentina API."""


class SMNError(Exception):
    """Base exception for SMN API errors."""


class SMNConnectionError(SMNError):
    """Exception raised when connection to SMN API fails."""


class SMNAuthenticationError(SMNError):
    """Exception raised when authentication with SMN API fails."""


class SMNTokenError(SMNError):
    """Exception raised when token fetching or parsing fails."""
