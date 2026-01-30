"""
Custom exceptions for the Volare Signals API client.

This module defines a hierarchy of exceptions that can be raised by the
API client, allowing for granular error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from volare_signals.models import ErrorResponse, RateLimitInfo


class VolareAPIError(Exception):
    """
    Base exception for all Volare API errors.

    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code, if applicable.
        error_code: Machine-readable error code from the API.
        details: Additional error details.
        field: The field that caused the error (for validation errors).
        rate_limit: Rate limit info from the response, if available.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
        details: str | None = None,
        field: str | None = None,
        rate_limit: RateLimitInfo | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        self.field = field
        self.rate_limit = rate_limit

    @classmethod
    def from_response(
        cls,
        error_response: ErrorResponse,
        status_code: int,
        rate_limit: RateLimitInfo | None = None,
    ) -> VolareAPIError:
        """
        Create an appropriate exception from an API error response.

        Args:
            error_response: Parsed error response from the API.
            status_code: HTTP status code.
            rate_limit: Rate limit information from headers.

        Returns:
            An instance of the appropriate exception subclass.
        """
        exception_class = _STATUS_CODE_EXCEPTIONS.get(status_code, cls)
        return exception_class(
            message=error_response.message,
            status_code=status_code,
            error_code=error_response.error,
            details=error_response.details,
            field=error_response.field,
            rate_limit=rate_limit,
        )

    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.insert(0, f"[{self.error_code}]")
        if self.status_code:
            parts.insert(0, f"HTTP {self.status_code}:")
        if self.field:
            parts.append(f"(field: {self.field})")
        if self.details:
            parts.append(f"- {self.details}")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code!r})"
        )


class ValidationError(VolareAPIError):
    """
    Raised when the API returns a 400 validation error.

    This typically indicates invalid query parameters or request body.
    Check the `field` attribute to identify which parameter caused the error.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str | None = None,
        details: str | None = None,
        field: str | None = None,
        rate_limit: RateLimitInfo | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code or "VALIDATION_ERROR",
            details=details,
            field=field,
            rate_limit=rate_limit,
        )


class AuthenticationError(VolareAPIError):
    """
    Raised when the API returns a 401 unauthorized error.

    This indicates that the API key is missing or invalid.
    Ensure you're using a valid API key with the format 'vk_...'.
    """

    def __init__(
        self,
        message: str = "Invalid or missing API key",
        status_code: int = 401,
        error_code: str | None = None,
        details: str | None = None,
        field: str | None = None,
        rate_limit: RateLimitInfo | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code or "UNAUTHORIZED",
            details=details,
            field=field,
            rate_limit=rate_limit,
        )


class ForbiddenError(VolareAPIError):
    """
    Raised when the API returns a 403 forbidden error.

    This indicates that the API key has been revoked or has expired.
    Contact support or generate a new API key.
    """

    def __init__(
        self,
        message: str = "API key revoked or expired",
        status_code: int = 403,
        error_code: str | None = None,
        details: str | None = None,
        field: str | None = None,
        rate_limit: RateLimitInfo | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code or "FORBIDDEN",
            details=details,
            field=field,
            rate_limit=rate_limit,
        )


class RateLimitExceededError(VolareAPIError):
    """
    Raised when the API returns a 429 rate limit exceeded error.

    Check the `rate_limit` attribute for information about when the
    rate limit will reset. The client includes automatic retry logic
    for this error type.

    Attributes:
        retry_after: Seconds to wait before retrying, if provided by the API.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: int = 429,
        error_code: str | None = None,
        details: str | None = None,
        field: str | None = None,
        rate_limit: RateLimitInfo | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code or "RATE_LIMIT_EXCEEDED",
            details=details,
            field=field,
            rate_limit=rate_limit,
        )
        self.retry_after = retry_after

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            return f"{base} (retry after {self.retry_after}s)"
        return base


class ServerError(VolareAPIError):
    """
    Raised when the API returns a 500 internal server error.

    This indicates a problem on the server side. The request can be
    retried, but if the problem persists, contact support.
    """

    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = 500,
        error_code: str | None = None,
        details: str | None = None,
        field: str | None = None,
        rate_limit: RateLimitInfo | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code or "SERVER_ERROR",
            details=details,
            field=field,
            rate_limit=rate_limit,
        )


class NetworkError(VolareAPIError):
    """
    Raised when a network-level error occurs.

    This could be a connection timeout, DNS resolution failure,
    or other transport-level issues.
    """

    def __init__(
        self,
        message: str = "Network error occurred",
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(message=message)
        self.original_error = original_error

    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message}: {self.original_error}"
        return self.message


class RetryExhaustedError(VolareAPIError):
    """
    Raised when all retry attempts have been exhausted.

    This is raised after the client has attempted the configured
    number of retries and all have failed.

    Attributes:
        attempts: Number of attempts made.
        last_error: The last error that occurred.
    """

    def __init__(
        self,
        message: str = "All retry attempts exhausted",
        attempts: int = 0,
        last_error: Exception | None = None,
    ) -> None:
        super().__init__(message=message)
        self.attempts = attempts
        self.last_error = last_error

    def __str__(self) -> str:
        result = f"{self.message} after {self.attempts} attempts"
        if self.last_error:
            result += f": {self.last_error}"
        return result


# Mapping of HTTP status codes to exception classes
_STATUS_CODE_EXCEPTIONS: dict[int, type[VolareAPIError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: ForbiddenError,
    429: RateLimitExceededError,
    500: ServerError,
}


def get_exception_for_status(status_code: int) -> type[VolareAPIError]:
    """
    Get the appropriate exception class for an HTTP status code.

    Args:
        status_code: The HTTP status code.

    Returns:
        The exception class to use for this status code.
    """
    return _STATUS_CODE_EXCEPTIONS.get(status_code, VolareAPIError)
