# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""HTTP transport layer for AAS Registry client.

This module provides synchronous and asynchronous HTTP transports that handle
communication with the AAS Registry API, including URL management, authentication
headers, and error mapping.
"""

from __future__ import annotations

from typing import Any

import httpx

from basyx_registry_client.exceptions import (
    RegistryAPIError,
    RegistryConnectionError,
)


def _parse_error_body(response: httpx.Response) -> dict[str, Any] | None:
    """Attempt to parse the response body as JSON.

    Args:
        response: The HTTP response to parse.

    Returns:
        The parsed JSON body as a dictionary, or None if parsing fails.
    """
    try:
        return response.json()  # type: ignore[no-any-return]
    except Exception:
        return None


class HTTPTransport:
    """Synchronous HTTP transport using httpx.

    Handles base URL management, authentication headers, and error mapping.
    Supports context manager protocol for proper resource cleanup.

    Example:
        >>> with HTTPTransport("http://localhost:8082/api/v3.0") as transport:
        ...     response = transport.request("GET", "/shell-descriptors")
        ...     data = response.json()
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        auth: httpx.Auth | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        """Initialize the transport.

        Args:
            base_url: Base URL of the registry API (e.g., "http://localhost:8082/api/v3.0")
            headers: Additional headers to include (e.g., authentication)
            timeout: Request timeout in seconds
            auth: Optional httpx authentication
            client: Optional pre-configured httpx.Client
        """
        self._base_url = base_url.rstrip("/")
        self._headers = headers or {}
        self._timeout = timeout
        self._auth = auth
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=self._base_url,
            headers=self._headers,
            timeout=timeout,
            auth=auth,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> httpx.Response:
        """Make an HTTP request, handling errors.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: URL path relative to base URL (e.g., "/shell-descriptors")
            params: Query parameters to include
            json: JSON body to send

        Returns:
            The httpx.Response object for successful requests.

        Raises:
            RegistryConnectionError: For network failures (timeouts, DNS errors, etc.)
            RegistryAPIError: For API error responses (4xx, 5xx status codes)
            NotFoundError: For 404 responses
            ConflictError: For 409 responses
            ValidationError: For 400 responses
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"

        try:
            response = self._client.request(
                method,
                path,
                params=params,
                json=json,
            )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            body = _parse_error_body(e.response)
            raise RegistryAPIError.from_response(e.response.status_code, body) from e
        except httpx.RequestError as e:
            raise RegistryConnectionError(f"Connection failed: {e}") from e

    def close(self) -> None:
        """Close the underlying HTTP client.

        Only closes the client if it was created by this transport.
        If a pre-configured client was passed to __init__, it will not be closed.
        """
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> HTTPTransport:
        """Enter the context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the context manager, closing the client."""
        self.close()


class AsyncHTTPTransport:
    """Asynchronous HTTP transport using httpx.

    Same interface as HTTPTransport but async. Handles base URL management,
    authentication headers, and error mapping.
    Supports async context manager protocol for proper resource cleanup.

    Example:
        >>> async with AsyncHTTPTransport("http://localhost:8082/api/v3.0") as transport:
        ...     response = await transport.request("GET", "/shell-descriptors")
        ...     data = response.json()
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        auth: httpx.Auth | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the transport.

        Args:
            base_url: Base URL of the registry API (e.g., "http://localhost:8082/api/v3.0")
            headers: Additional headers to include (e.g., authentication)
            timeout: Request timeout in seconds
            auth: Optional httpx authentication
            client: Optional pre-configured httpx.AsyncClient
        """
        self._base_url = base_url.rstrip("/")
        self._headers = headers or {}
        self._timeout = timeout
        self._auth = auth
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=timeout,
            auth=auth,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> httpx.Response:
        """Make an HTTP request, handling errors.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: URL path relative to base URL (e.g., "/shell-descriptors")
            params: Query parameters to include
            json: JSON body to send

        Returns:
            The httpx.Response object for successful requests.

        Raises:
            RegistryConnectionError: For network failures (timeouts, DNS errors, etc.)
            RegistryAPIError: For API error responses (4xx, 5xx status codes)
            NotFoundError: For 404 responses
            ConflictError: For 409 responses
            ValidationError: For 400 responses
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"

        try:
            response = await self._client.request(
                method,
                path,
                params=params,
                json=json,
            )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            body = _parse_error_body(e.response)
            raise RegistryAPIError.from_response(e.response.status_code, body) from e
        except httpx.RequestError as e:
            raise RegistryConnectionError(f"Connection failed: {e}") from e

    async def aclose(self) -> None:
        """Close the underlying async HTTP client.

        Only closes the client if it was created by this transport.
        If a pre-configured client was passed to __init__, it will not be closed.
        """
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTPTransport:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit the async context manager, closing the client."""
        await self.aclose()
