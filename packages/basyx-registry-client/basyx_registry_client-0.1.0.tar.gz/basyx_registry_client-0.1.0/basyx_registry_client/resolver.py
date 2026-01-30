# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Endpoint resolution logic for AAS Registry descriptors.

This module provides logic to select the best endpoint from a descriptor
based on interface and protocol preferences. Used by the RegistryClient
to resolve URLs from descriptor responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from basyx_registry_client.models import Endpoint


@dataclass
class ResolverConfig:
    """Configuration for endpoint resolution.

    Attributes:
        preferred_interface: Interface type to prefer (e.g., "AAS-3.0", "SUBMODEL-3.0").
            If specified, endpoints with this interface receive +2 points.
        preferred_protocol: Protocol to prefer (e.g., "HTTPS", "HTTP").
            If specified, endpoints with this protocol receive +1 point.
            Comparison is case-insensitive and falls back to URL scheme if
            endpointProtocol is not provided.
        fallback_to_any: If True, return any endpoint when preferred not found.
            If False, return None when no endpoint matches preferences.
            Defaults to True.
    """

    preferred_interface: str | None = None
    preferred_protocol: str | None = None
    fallback_to_any: bool = True


def _protocol_from_endpoint(endpoint: Endpoint) -> str | None:
    """Normalize endpoint protocol, falling back to URL scheme when needed."""
    protocol = endpoint.protocol_information.endpoint_protocol
    if protocol:
        return protocol.upper()

    href = endpoint.protocol_information.href
    scheme = urlparse(href).scheme
    if not scheme:
        return None
    return scheme.upper()


def _score_endpoint(endpoint: Endpoint, config: ResolverConfig) -> int:
    """Calculate a score for an endpoint based on configuration preferences.

    Args:
        endpoint: The endpoint to score.
        config: The resolver configuration with preferences.

    Returns:
        Integer score: +2 for interface match, +1 for protocol match.
    """
    score = 0

    # +2 points for matching preferred_interface (exact match)
    if config.preferred_interface is not None and endpoint.interface == config.preferred_interface:
        score += 2

    # +1 point for matching preferred_protocol (case-insensitive)
    endpoint_protocol = _protocol_from_endpoint(endpoint)
    if (
        config.preferred_protocol is not None
        and endpoint_protocol is not None
        and endpoint_protocol == config.preferred_protocol.upper()
    ):
        score += 1

    return score


def resolve_endpoint(
    endpoints: list[Endpoint],
    config: ResolverConfig | None = None,
) -> str | None:
    """Select the best endpoint URL from a list based on configuration.

    The selection algorithm:
    1. Score each endpoint based on interface and protocol matches
    2. Return the href of the highest-scoring endpoint
    3. If no endpoints match and fallback_to_any=False, return None
    4. If no endpoints match and fallback_to_any=True, prefer HTTPS endpoint if present,
       otherwise return first endpoint's href

    Scoring:
    - +2 points for matching preferred_interface (exact match required)
    - +1 point for matching preferred_protocol (case-insensitive comparison)
    - When no preferences match and fallback is allowed, HTTPS is preferred by scheme
      if available (unless preferred_protocol is explicitly set)

    Args:
        endpoints: List of Endpoint objects to choose from.
        config: Optional resolver configuration. If None, uses default config
            with fallback_to_any=True.

    Returns:
        URL string of the best matching endpoint, or None if no suitable endpoint found.

    Examples:
        >>> from basyx_registry_client.models import Endpoint, ProtocolInformation
        >>> endpoints = [
        ...     Endpoint(
        ...         interface="AAS-3.0",
        ...         protocol_information=ProtocolInformation(
        ...             href="https://example.com/aas",
        ...             endpoint_protocol="HTTPS"
        ...         )
        ...     ),
        ...     Endpoint(
        ...         interface="AAS-3.0",
        ...         protocol_information=ProtocolInformation(
        ...             href="http://example.com/aas",
        ...             endpoint_protocol="HTTP"
        ...         )
        ...     ),
        ... ]
        >>> config = ResolverConfig(preferred_interface="AAS-3.0", preferred_protocol="HTTPS")
        >>> resolve_endpoint(endpoints, config)
        'https://example.com/aas'

        With no preferences, returns first endpoint:

        >>> resolve_endpoint(endpoints)
        'https://example.com/aas'

        With fallback_to_any=False and no match:

        >>> config = ResolverConfig(preferred_interface="OTHER", fallback_to_any=False)
        >>> resolve_endpoint(endpoints, config) is None
        True
    """
    # Handle empty list
    if not endpoints:
        return None

    # Use default config if none provided
    if config is None:
        config = ResolverConfig()

    # Score all endpoints
    scored_endpoints: list[tuple[int, Endpoint]] = [
        (_score_endpoint(ep, config), ep) for ep in endpoints
    ]

    # Find the maximum score
    max_score = max(score for score, _ in scored_endpoints)

    # Collect candidates with the max score
    candidates = [endpoint for score, endpoint in scored_endpoints if score == max_score]

    # If max score is 0, no endpoint matched preferences
    if max_score == 0:
        if not config.fallback_to_any:
            return None
        # Prefer HTTPS by scheme when no explicit protocol preference is set
        if config.preferred_protocol is None:
            for endpoint in candidates:
                if _protocol_from_endpoint(endpoint) == "HTTPS":
                    return endpoint.protocol_information.href
        # Fall back to first endpoint
        return candidates[0].protocol_information.href

    # Return the first best endpoint, preferring HTTPS on ties when no protocol preference
    if config.preferred_protocol is None and len(candidates) > 1:
        for endpoint in candidates:
            if _protocol_from_endpoint(endpoint) == "HTTPS":
                return endpoint.protocol_information.href
    return candidates[0].protocol_information.href

    # This should never be reached, but satisfies type checker
    return None  # pragma: no cover
