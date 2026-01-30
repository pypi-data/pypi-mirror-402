"""
Base endpoint class for AAS Part 2 API endpoints.

Provides common functionality for HTTP requests, error handling,
and response parsing that all endpoint implementations share.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import httpx

from basyx_client.exceptions import (
    ConnectionError,
    TimeoutError,
    map_status_to_exception,
)

if TYPE_CHECKING:
    from basyx_client.client import AASClient


class BaseEndpoint:
    """
    Base class for all endpoint namespaces.

    Provides unified HTTP request methods with:
    - Automatic error handling and exception mapping
    - Support for both sync and async operations
    - Response JSON parsing

    Subclasses should use _request() and _request_async() for all HTTP calls.
    """

    def __init__(self, client: AASClient) -> None:
        """
        Initialize the endpoint with a reference to the parent client.

        Args:
            client: The AASClient instance this endpoint belongs to
        """
        self._client = client

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Make a synchronous HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            path: URL path (will be appended to base_url)
            params: Query parameters
            json: JSON body (for POST, PUT, PATCH)
            content: Raw content body
            headers: Additional headers

        Returns:
            Parsed JSON response, or None if response has no body

        Raises:
            ResourceNotFoundError: If resource not found (404)
            BadRequestError: If request is invalid (400)
            ConflictError: If resource conflict (409)
            UnauthorizedError: If authentication required (401)
            ForbiddenError: If access denied (403)
            ServerError: If server error (5xx)
            ConnectionError: If unable to connect
            TimeoutError: If request times out
        """
        url = f"{self._client.base_url}{path}"

        try:
            response = self._client._sync_client.request(
                method,
                url,
                params=params,
                json=json,
                content=content,
                headers=headers,
            )
            return self._handle_response(response, url)

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Failed to connect to {url}: {e}",
                url=url,
            ) from e
        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"Request timed out: {url}",
                url=url,
            ) from e

    async def _request_async(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Make an asynchronous HTTP request.

        Same interface as _request() but async.
        """
        url = f"{self._client.base_url}{path}"

        try:
            response = await self._client._async_client.request(
                method,
                url,
                params=params,
                json=json,
                content=content,
                headers=headers,
            )
            return self._handle_response(response, url)

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Failed to connect to {url}: {e}",
                url=url,
            ) from e
        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"Request timed out: {url}",
                url=url,
            ) from e

    def _handle_response(
        self,
        response: httpx.Response,
        url: str,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Handle HTTP response - check for errors and parse JSON.

        Args:
            response: The HTTP response
            url: The request URL (for error messages)

        Returns:
            Parsed JSON response, or None if no content

        Raises:
            Appropriate exception based on status code
        """
        if response.is_success:
            if response.status_code == 204 or not response.content:
                return None
            result = response.json()
            return cast("dict[str, Any] | list[Any]", result)

        # Extract error details from response body if available
        details = None
        message = f"HTTP {response.status_code}"
        try:
            error_body = response.json()
            if isinstance(error_body, dict):
                details = error_body
                extracted = error_body.get("message") or error_body.get("error")
                if extracted:
                    message = str(extracted)
        except Exception:
            # Response body wasn't JSON
            if response.text:
                message = response.text[:200]

        raise map_status_to_exception(
            status_code=response.status_code,
            message=message,
            url=url,
            details=details,
        )
