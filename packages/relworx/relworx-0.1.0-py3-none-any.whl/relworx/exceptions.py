"""
Custom exceptions for the Relworx SDK.
"""


class RelworxError(Exception):
    """Base exception for all Relworx SDK errors."""

    pass


class AuthenticationError(RelworxError):
    """Raised when authentication fails."""

    pass


class ValidationError(RelworxError):
    """Raised when request validation fails."""

    pass


class APIError(RelworxError):
    """Raised when the API returns an error."""

    def __init__(self, message, status_code=None, response_data=None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)
