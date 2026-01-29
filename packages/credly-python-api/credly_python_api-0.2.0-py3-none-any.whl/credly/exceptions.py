"""Custom exceptions for the Credly API client."""


class CredlyAPIError(Exception):
    """Base exception for all Credly API errors."""

    def __init__(self, message, status_code=None, response=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class UnauthorizedError(CredlyAPIError):
    """Raised when API returns 401 Unauthorized."""

    pass


class ForbiddenError(CredlyAPIError):
    """Raised when API returns 403 Forbidden."""

    pass


class NotFoundError(CredlyAPIError):
    """Raised when API returns 404 Not Found."""

    pass


class ValidationError(CredlyAPIError):
    """Raised when API returns 422 Unprocessable Entity (validation error)."""

    pass


class RateLimitError(CredlyAPIError):
    """Raised when API returns 429 Too Many Requests."""

    pass
