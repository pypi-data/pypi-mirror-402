# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Base64URL encoding/decoding utilities for AAS Registry API.

Per IDTA-01002, identifiers in URL paths must be base64url-encoded.
This module provides functions to encode and decode these identifiers.

The base64url encoding uses URL-safe characters (- instead of +, _ instead of /)
and omits padding (= signs) as specified in RFC 4648 Section 5.
"""

from __future__ import annotations

import base64


def base64url_encode(value: str) -> str:
    """Encode a string to base64url without padding.

    Per IDTA-01002, IDs in URLs must be base64url-encoded using the
    URL-safe alphabet (RFC 4648 Section 5) without padding.

    Args:
        value: The string to encode (typically an AAS or Submodel ID).

    Returns:
        The base64url-encoded string without padding.

    Examples:
        >>> base64url_encode("https://example.org/aas/123")
        'aHR0cHM6Ly9leGFtcGxlLm9yZy9hYXMvMTIz'
        >>> base64url_encode("urn:example:aas:1")
        'dXJuOmV4YW1wbGU6YWFzOjE'
    """
    # Encode string to bytes, then to base64url
    encoded_bytes = base64.urlsafe_b64encode(value.encode("utf-8"))
    # Convert to string and strip padding
    return encoded_bytes.decode("ascii").rstrip("=")


def base64url_decode(encoded: str) -> str:
    """Decode a base64url-encoded string.

    Handles missing padding gracefully by adding the required padding
    characters before decoding.

    Args:
        encoded: The base64url-encoded string (with or without padding).

    Returns:
        The decoded string.

    Raises:
        ValueError: If the input is not valid base64url.

    Examples:
        >>> base64url_decode("aHR0cHM6Ly9leGFtcGxlLm9yZy9hYXMvMTIz")
        'https://example.org/aas/123'
        >>> base64url_decode("dXJuOmV4YW1wbGU6YWFzOjE")
        'urn:example:aas:1'
    """
    # Add padding if needed (base64 requires length to be multiple of 4)
    padding_needed = (4 - len(encoded) % 4) % 4
    padded = encoded + "=" * padding_needed

    try:
        decoded_bytes = base64.urlsafe_b64decode(padded)
        return decoded_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Invalid base64url string: {encoded}") from e
