# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Integration with basyx-client for AAS repository access.

This module provides convenience functions to create basyx-client AASClient
instances from registry descriptors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from basyx_registry_client.client import RegistryClient

if TYPE_CHECKING:
    # Only import for type hints to avoid hard dependency
    from basyx_client import AASClient  # type: ignore[import-untyped]


def aas_client_from_registry(
    registry_client: RegistryClient,
    aas_id: str,
    *,
    interface: str | None = None,
    protocol: str | None = None,
) -> AASClient:
    """Create an AASClient by resolving the endpoint from the registry.

    This function:
    1. Fetches the AAS descriptor from the registry
    2. Resolves the best endpoint URL based on preferences
    3. Creates and returns an AASClient pointing to that endpoint

    Args:
        registry_client: A RegistryClient instance
        aas_id: The AAS identifier to resolve
        interface: Override preferred interface (e.g., "AAS-3.0")
        protocol: Override preferred protocol (e.g., "HTTPS")

    Returns:
        An AASClient instance configured for the resolved endpoint

    Raises:
        ImportError: If basyx-client is not installed
        ValueError: If no suitable endpoint is found
        NotFoundError: If the AAS is not registered

    Example:
        >>> from basyx_registry_client import RegistryClient
        >>> from basyx_registry_client.integrations import aas_client_from_registry
        >>>
        >>> registry = RegistryClient("http://registry:8082/api/v3.0")
        >>> client = aas_client_from_registry(registry, "urn:example:aas:1")
        >>> # client is now configured to talk to the AAS server
        >>> shells = client.list_shells()
    """
    try:
        from basyx_client import AASClient as AASClientClass
    except ImportError as e:
        raise ImportError(
            "basyx-client is required for this integration. "
            "Install it with: pip install basyx-registry-client[basyx]"
        ) from e

    # Resolve the endpoint URL
    href = registry_client.resolve_aas_href(aas_id, interface=interface, protocol=protocol)

    if href is None:
        raise ValueError(
            f"No suitable endpoint found for AAS '{aas_id}'. "
            "Check that the descriptor has endpoints matching your preferences."
        )

    result: Any = AASClientClass(href)
    return result
