"""
Exceptions for the VibeKit API client.
"""


class VKClientError(Exception):
    """Base exception for VK client errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response or {}


class AuthenticationError(VKClientError):
    """Raised when authentication fails or token is invalid."""

    def __init__(self, message: str = "Authentication required. Run 'vk login' to authenticate."):
        super().__init__(message, status_code=401)


class NotFoundError(VKClientError):
    """Raised when a resource is not found."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", status_code=404)


class RateLimitError(VKClientError):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ServerError(VKClientError):
    """Raised when the server returns a 5xx error."""

    def __init__(self, message: str = "Server error. Please try again later."):
        super().__init__(message, status_code=500)


class ValidationError(VKClientError):
    """Raised when request validation fails."""

    def __init__(self, errors: dict = None):
        message = "Validation error"
        if errors:
            message += f": {errors}"
        super().__init__(message, status_code=422)
        self.errors = errors or {}


class OfflineError(VKClientError):
    """Raised when the client cannot connect to the server."""

    def __init__(self):
        super().__init__(
            "Cannot connect to vkcli.com. Please check your internet connection.", status_code=0
        )
