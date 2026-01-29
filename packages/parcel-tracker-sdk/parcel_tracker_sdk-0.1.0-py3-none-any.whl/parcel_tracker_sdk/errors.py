"""Custom exceptions for ParcelTracker SDK."""


class ParcelTrackerError(Exception):
    """Base exception for ParcelTracker SDK errors."""

    def __init__(self, message: str):
        """Initialize the exception."""
        self.message = message
        super().__init__(message)


class APIError(ParcelTrackerError):
    """Exception raised for API errors."""

    pass


class ValidationError(ParcelTrackerError):
    """Exception raised for validation errors."""

    pass


class AuthenticationError(ParcelTrackerError):
    """Exception raised for authentication errors."""

    pass


class RateLimitError(ParcelTrackerError):
    """Exception raised for rate limit errors."""

    pass


class NotFoundError(ParcelTrackerError):
    """Exception raised when a resource is not found."""

    pass
