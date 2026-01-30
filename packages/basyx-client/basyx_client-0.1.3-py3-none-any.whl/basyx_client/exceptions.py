"""
Exception hierarchy for AAS Part 2 API client.

Provides typed exceptions for each category of error, enabling
precise error handling without checking status codes manually.

Example:
    try:
        aas = client.shells.get("urn:example:aas:123")
    except ResourceNotFoundError:
        # Handle 404
        pass
    except UnauthorizedError:
        # Handle 401
        pass
"""

from typing import Any


class AASClientError(Exception):
    """
    Base exception for all AAS client errors.

    Attributes:
        message: Human-readable error description
        status_code: HTTP status code (if applicable)
        url: The URL that was requested (if applicable)
        details: Additional error details from the API response
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        url: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.url = url
        self.details = details or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"[{self.status_code}]")
        if self.url:
            parts.append(f"URL: {self.url}")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"url={self.url!r})"
        )


class ResourceNotFoundError(AASClientError):
    """
    Resource not found (HTTP 404).

    Raised when requesting an AAS, Submodel, or SubmodelElement
    that does not exist.
    """

    pass


class BadRequestError(AASClientError):
    """
    Bad request (HTTP 400).

    Raised when the request is malformed or contains invalid data.
    Check the `details` attribute for specific validation errors.
    """

    pass


class ConflictError(AASClientError):
    """
    Conflict (HTTP 409).

    Raised when attempting to create a resource that already exists
    or when there's a version conflict during update.
    """

    pass


class UnauthorizedError(AASClientError):
    """
    Unauthorized (HTTP 401).

    Raised when authentication is required but not provided,
    or when the provided credentials are invalid.
    """

    pass


class ForbiddenError(AASClientError):
    """
    Forbidden (HTTP 403).

    Raised when the authenticated user does not have permission
    to perform the requested operation.
    """

    pass


class ServerError(AASClientError):
    """
    Server error (HTTP 5xx).

    Raised when the server encounters an internal error.
    """

    pass


class ConnectionError(AASClientError):
    """
    Connection error.

    Raised when unable to connect to the server (network issues,
    DNS resolution failure, etc.).
    """

    pass


class TimeoutError(AASClientError):
    """
    Request timeout.

    Raised when the request exceeds the configured timeout.
    """

    pass


def map_status_to_exception(
    status_code: int,
    message: str,
    url: str | None = None,
    details: dict[str, Any] | None = None,
) -> AASClientError:
    """
    Map an HTTP status code to the appropriate exception type.

    Args:
        status_code: HTTP status code
        message: Error message
        url: Request URL
        details: Additional error details

    Returns:
        Appropriate AASClientError subclass instance
    """
    exception_map: dict[int, type[AASClientError]] = {
        400: BadRequestError,
        401: UnauthorizedError,
        403: ForbiddenError,
        404: ResourceNotFoundError,
        409: ConflictError,
    }

    if status_code in exception_map:
        return exception_map[status_code](message, status_code, url, details)
    elif 500 <= status_code < 600:
        return ServerError(message, status_code, url, details)
    else:
        return AASClientError(message, status_code, url, details)
