"""
Custom exceptions for ActorHub SDK.
"""

from typing import Optional, Dict, Any


class ActorHubError(Exception):
    """Base exception for ActorHub SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        self.request_id = request_id

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.request_id:
            parts.append(f"[Request ID: {self.request_id}]")
        return " ".join(parts)


class AuthenticationError(ActorHubError):
    """Raised when API key is invalid or missing."""

    def __init__(
        self,
        message: str = "Invalid or missing API key",
        **kwargs: Any,
    ):
        super().__init__(message, status_code=401, **kwargs)


class RateLimitError(ActorHubError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class ValidationError(ActorHubError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(message, status_code=422, **kwargs)
        self.errors = errors or {}


class NotFoundError(ActorHubError):
    """Raised when requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        **kwargs: Any,
    ):
        super().__init__(message, status_code=404, **kwargs)


class ServerError(ActorHubError):
    """Raised when server returns 5xx error."""

    def __init__(
        self,
        message: str = "Server error",
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
