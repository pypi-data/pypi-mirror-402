"""Exception hierarchy for the Supermicro Redfish client."""

from __future__ import annotations


class SupermicroRedfishError(Exception):
    """Base exception for all Supermicro Redfish client errors."""


class ConnectionError(SupermicroRedfishError):
    """Failed to connect to the BMC.

    Raised when network issues prevent communication with the BMC.
    """


class TimeoutError(SupermicroRedfishError):
    """Request timeout.

    Raised when a request exceeds the configured timeout.
    """


class AuthenticationError(SupermicroRedfishError):
    """Authentication failed (HTTP 401).

    Raised when credentials are invalid or the session has expired.
    """


class AuthorizationError(SupermicroRedfishError):
    """Not authorized for this operation (HTTP 403).

    Raised when valid credentials lack sufficient permissions.
    """


class NotFoundError(SupermicroRedfishError):
    """Requested resource not found (HTTP 404).

    Raised when an endpoint or resource does not exist.
    """


class InvalidRequestError(SupermicroRedfishError):
    """Bad request (HTTP 400).

    Raised when the request is malformed or contains invalid parameters.
    """


class RateLimitError(SupermicroRedfishError):
    """Too many requests (HTTP 429).

    Raised when the BMC rate limits the client.
    """


class ServiceUnavailableError(SupermicroRedfishError):
    """Service temporarily unavailable (HTTP 503).

    Raised when the BMC is temporarily unable to handle requests.
    """


class InvalidResponseError(SupermicroRedfishError):
    """Unexpected response format.

    Raised when the BMC returns data that cannot be parsed.
    """


# Map HTTP status codes to exception classes
HTTP_STATUS_EXCEPTIONS: dict[int, type[SupermicroRedfishError]] = {
    400: InvalidRequestError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    429: RateLimitError,
    503: ServiceUnavailableError,
}


def raise_for_status(status: int, message: str = "") -> None:
    """Raise appropriate exception for HTTP status code.

    Args:
        status: HTTP status code
        message: Optional error message

    Raises:
        SupermicroRedfishError: If status >= 400
    """
    if status >= 400:
        exc_class = HTTP_STATUS_EXCEPTIONS.get(status, SupermicroRedfishError)
        raise exc_class(message or f"HTTP {status}")
