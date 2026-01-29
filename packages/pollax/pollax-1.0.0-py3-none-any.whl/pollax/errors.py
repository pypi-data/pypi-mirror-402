"""Custom exceptions for Pollax SDK"""


class PollaxError(Exception):
    """Base exception for all Pollax errors."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(PollaxError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class NotFoundError(PollaxError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class RateLimitError(PollaxError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class ValidationError(PollaxError):
    """Raised for validation errors."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=400)
