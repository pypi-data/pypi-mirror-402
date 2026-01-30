# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Exception hierarchy for AAS Registry client errors.

This module provides typed exceptions that map to API error responses,
enabling precise error handling in client code.

The AAS Registry API returns error bodies in the format:
    {"type": "ErrorType", "message": "Error description"}

These are parsed into appropriate exception types based on HTTP status codes.
"""

from __future__ import annotations

from typing import Any


class RegistryError(Exception):
    """Base exception for all registry client errors.

    All exceptions raised by the registry client inherit from this class,
    enabling catch-all error handling when needed.
    """

    pass


class RegistryConnectionError(RegistryError):
    """Network or connection errors.

    Raised when the client cannot connect to the registry server,
    such as DNS resolution failures, connection timeouts, or network
    unreachability.

    Examples:
        - Server is unreachable
        - Connection timeout
        - DNS resolution failed
        - SSL/TLS handshake failed
    """

    pass


class RegistryAPIError(RegistryError):
    """API returned an error response.

    Raised when the registry server responds with an HTTP error status code.
    Contains details from the error response body when available.

    Attributes:
        status_code: The HTTP status code returned by the server.
        error_type: The error type from the response body (e.g., "InvalidArgument").
        message: The error message from the response body.
        response_body: The raw response body, if available.
    """

    def __init__(
        self,
        status_code: int,
        error_type: str | None = None,
        message: str | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the API error.

        Args:
            status_code: The HTTP status code.
            error_type: The error type from the response body.
            message: The error message from the response body.
            response_body: The raw response body dictionary.
        """
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.response_body = response_body

        # Build a descriptive error message
        parts = [f"HTTP {status_code}"]
        if error_type:
            parts.append(f"[{error_type}]")
        if message:
            parts.append(message)
        super().__init__(" ".join(parts))

    @classmethod
    def from_response(
        cls, status_code: int, body: dict[str, Any] | None = None
    ) -> RegistryAPIError:
        """Create an appropriate exception from an HTTP response.

        This factory method parses the error response body and returns
        the appropriate exception subclass based on the status code.

        Args:
            status_code: The HTTP status code.
            body: The parsed JSON response body, if available.

        Returns:
            An instance of the appropriate RegistryAPIError subclass.
        """
        error_type = body.get("type") if body else None
        message = body.get("message") if body else None

        # Map status codes to specific exception types
        exception_class: type[RegistryAPIError]
        if status_code == 400:
            exception_class = ValidationError
        elif status_code == 404:
            exception_class = NotFoundError
        elif status_code == 409:
            exception_class = ConflictError
        else:
            exception_class = cls

        return exception_class(
            status_code=status_code,
            error_type=error_type,
            message=message,
            response_body=body,
        )


class NotFoundError(RegistryAPIError):
    """Resource not found (HTTP 404).

    Raised when the requested AAS descriptor or submodel descriptor
    does not exist in the registry.

    Examples:
        - AAS descriptor with given ID not found
        - Submodel descriptor with given ID not found
    """

    pass


class ConflictError(RegistryAPIError):
    """Resource already exists (HTTP 409).

    Raised when attempting to create a resource that already exists,
    such as registering an AAS descriptor with an ID that is already
    in the registry.

    Examples:
        - AAS descriptor with given ID already exists
        - Submodel descriptor with given ID already exists
    """

    pass


class ValidationError(RegistryAPIError):
    """Invalid request data (HTTP 400).

    Raised when the request data fails validation, such as malformed
    identifiers or invalid descriptor structures.

    Examples:
        - Invalid AAS ID format
        - Missing required fields in descriptor
        - Invalid endpoint URL format
    """

    pass
