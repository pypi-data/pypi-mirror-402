"""Exceptions for the NeuraLex client library."""


class NeuraLexError(Exception):
    """Base exception for all NeuraLex errors."""

    pass


class AuthenticationError(NeuraLexError):
    """Raised when API key is invalid or missing."""

    pass


class RateLimitError(NeuraLexError):
    """Raised when rate limit is exceeded."""

    pass


class APIError(NeuraLexError):
    """Raised when the API returns an error response."""

    def __init__(self, message: str, status_code: int, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}
