# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Synchronous client for AAS Registry APIs.

This module provides the main RegistryClient class that wraps all AAS Registry
API operations defined in IDTA-01002 Part 2, v3.x.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx

from basyx_registry_client.encoding import base64url_encode
from basyx_registry_client.http import HTTPTransport
from basyx_registry_client.models import (
    AssetAdministrationShellDescriptor,
    ServiceDescription,
    SubmodelDescriptor,
)
from basyx_registry_client.pagination import PagedResult
from basyx_registry_client.resolver import ResolverConfig, resolve_endpoint


class RegistryClient:
    """Synchronous client for AAS Registry APIs (IDTA-01002 Part 2, v3.x).

    Provides methods for:
    - Service description
    - AAS descriptor CRUD operations
    - Submodel descriptor CRUD operations (standalone and nested)
    - Endpoint resolution

    Example:
        >>> client = RegistryClient("http://localhost:8082/api/v3.0")
        >>> description = client.get_description()
        >>> for descriptor in client.iter_shell_descriptors():
        ...     print(descriptor.id)
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        auth: httpx.Auth | None = None,
        client: httpx.Client | None = None,
        resolver_config: ResolverConfig | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            base_url: Base URL of the registry API
            headers: Additional headers (e.g., authentication)
            timeout: Request timeout in seconds
            auth: Optional httpx authentication
            client: Optional pre-configured httpx.Client (must set base_url)
            resolver_config: Configuration for endpoint resolution
        """
        self._transport = HTTPTransport(
            base_url,
            headers=headers,
            timeout=timeout,
            auth=auth,
            client=client,
        )
        self._resolver_config = resolver_config or ResolverConfig()

    # === Description API ===

    def get_description(self) -> ServiceDescription:
        """Get the service description."""
        response = self._transport.request("GET", "/description")
        return ServiceDescription.model_validate(response.json())

    # === Shell Descriptor API ===

    def list_shell_descriptors(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        id_short: str | None = None,
        asset_kind: str | None = None,
    ) -> PagedResult[AssetAdministrationShellDescriptor]:
        """List AAS descriptors with pagination.

        Args:
            limit: Maximum number of results per page
            cursor: Pagination cursor from previous response
            id_short: Optional idShort filter
            asset_kind: Optional assetKind filter (e.g., "Instance", "Type")

        Returns:
            PagedResult containing descriptors and cursor for next page
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        if id_short is not None:
            params["idShort"] = id_short
        if asset_kind is not None:
            params["assetKind"] = asset_kind

        response = self._transport.request("GET", "/shell-descriptors", params=params)
        data = response.json()

        items = [
            AssetAdministrationShellDescriptor.model_validate(item)
            for item in data.get("result", [])
        ]
        return PagedResult(items=items, cursor=self._extract_cursor(data))

    def iter_shell_descriptors(self) -> Iterator[AssetAdministrationShellDescriptor]:
        """Iterate over all AAS descriptors, handling pagination automatically."""
        cursor = None
        while True:
            page = self.list_shell_descriptors(cursor=cursor)
            yield from page
            if not page.has_more:
                break
            cursor = page.cursor

    def get_shell_descriptor(self, aas_id: str) -> AssetAdministrationShellDescriptor:
        """Get a specific AAS descriptor by ID.

        Args:
            aas_id: The AAS identifier (will be base64url-encoded)
        """
        encoded_id = base64url_encode(aas_id)
        response = self._transport.request("GET", f"/shell-descriptors/{encoded_id}")
        return AssetAdministrationShellDescriptor.model_validate(response.json())

    def register_shell_descriptor(
        self, descriptor: AssetAdministrationShellDescriptor
    ) -> AssetAdministrationShellDescriptor:
        """Register a new AAS descriptor.

        Args:
            descriptor: The descriptor to register

        Returns:
            The registered descriptor (may include server-generated fields)
        """
        response = self._transport.request(
            "POST",
            "/shell-descriptors",
            json=descriptor.model_dump(by_alias=True, exclude_none=True),
        )
        return AssetAdministrationShellDescriptor.model_validate(response.json())

    def update_shell_descriptor(
        self, aas_id: str, descriptor: AssetAdministrationShellDescriptor
    ) -> None:
        """Update an existing AAS descriptor.

        Args:
            aas_id: The AAS identifier
            descriptor: The updated descriptor
        """
        encoded_id = base64url_encode(aas_id)
        self._transport.request(
            "PUT",
            f"/shell-descriptors/{encoded_id}",
            json=descriptor.model_dump(by_alias=True, exclude_none=True),
        )

    def unregister_shell_descriptor(self, aas_id: str) -> None:
        """Remove an AAS descriptor from the registry.

        Args:
            aas_id: The AAS identifier
        """
        encoded_id = base64url_encode(aas_id)
        self._transport.request("DELETE", f"/shell-descriptors/{encoded_id}")

    # === Standalone Submodel Descriptor API ===

    def list_submodel_descriptors(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> PagedResult[SubmodelDescriptor]:
        """List standalone Submodel descriptors with pagination."""
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        response = self._transport.request("GET", "/submodel-descriptors", params=params)
        data = response.json()

        items = [SubmodelDescriptor.model_validate(item) for item in data.get("result", [])]
        return PagedResult(items=items, cursor=self._extract_cursor(data))

    def iter_submodel_descriptors(self) -> Iterator[SubmodelDescriptor]:
        """Iterate over all standalone Submodel descriptors."""
        cursor = None
        while True:
            page = self.list_submodel_descriptors(cursor=cursor)
            yield from page
            if not page.has_more:
                break
            cursor = page.cursor

    def get_submodel_descriptor(self, submodel_id: str) -> SubmodelDescriptor:
        """Get a specific Submodel descriptor by ID."""
        encoded_id = base64url_encode(submodel_id)
        response = self._transport.request("GET", f"/submodel-descriptors/{encoded_id}")
        return SubmodelDescriptor.model_validate(response.json())

    def register_submodel_descriptor(self, descriptor: SubmodelDescriptor) -> SubmodelDescriptor:
        """Register a new standalone Submodel descriptor."""
        response = self._transport.request(
            "POST",
            "/submodel-descriptors",
            json=descriptor.model_dump(by_alias=True, exclude_none=True),
        )
        return SubmodelDescriptor.model_validate(response.json())

    def update_submodel_descriptor(self, submodel_id: str, descriptor: SubmodelDescriptor) -> None:
        """Update an existing Submodel descriptor."""
        encoded_id = base64url_encode(submodel_id)
        self._transport.request(
            "PUT",
            f"/submodel-descriptors/{encoded_id}",
            json=descriptor.model_dump(by_alias=True, exclude_none=True),
        )

    def unregister_submodel_descriptor(self, submodel_id: str) -> None:
        """Remove a Submodel descriptor from the registry."""
        encoded_id = base64url_encode(submodel_id)
        self._transport.request("DELETE", f"/submodel-descriptors/{encoded_id}")

    # === Nested Submodel Descriptors (under an AAS) ===

    def list_submodel_descriptors_of_shell(
        self,
        aas_id: str,
        *,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> PagedResult[SubmodelDescriptor]:
        """List Submodel descriptors nested under an AAS."""
        encoded_aas_id = base64url_encode(aas_id)
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        response = self._transport.request(
            "GET",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors",
            params=params,
        )
        data = response.json()

        items = [SubmodelDescriptor.model_validate(item) for item in data.get("result", [])]
        return PagedResult(items=items, cursor=self._extract_cursor(data))

    def iter_submodel_descriptors_of_shell(self, aas_id: str) -> Iterator[SubmodelDescriptor]:
        """Iterate over all Submodel descriptors nested under an AAS."""
        cursor = None
        while True:
            page = self.list_submodel_descriptors_of_shell(aas_id, cursor=cursor)
            yield from page
            if not page.has_more:
                break
            cursor = page.cursor

    def get_submodel_descriptor_of_shell(self, aas_id: str, submodel_id: str) -> SubmodelDescriptor:
        """Get a specific Submodel descriptor nested under an AAS."""
        encoded_aas_id = base64url_encode(aas_id)
        encoded_sm_id = base64url_encode(submodel_id)
        response = self._transport.request(
            "GET",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors/{encoded_sm_id}",
        )
        return SubmodelDescriptor.model_validate(response.json())

    def add_submodel_descriptor_to_shell(
        self, aas_id: str, descriptor: SubmodelDescriptor
    ) -> SubmodelDescriptor:
        """Add a Submodel descriptor to an AAS."""
        encoded_aas_id = base64url_encode(aas_id)
        response = self._transport.request(
            "POST",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors",
            json=descriptor.model_dump(by_alias=True, exclude_none=True),
        )
        return SubmodelDescriptor.model_validate(response.json())

    def remove_submodel_descriptor_from_shell(self, aas_id: str, submodel_id: str) -> None:
        """Remove a Submodel descriptor from an AAS."""
        encoded_aas_id = base64url_encode(aas_id)
        encoded_sm_id = base64url_encode(submodel_id)
        self._transport.request(
            "DELETE",
            f"/shell-descriptors/{encoded_aas_id}/submodel-descriptors/{encoded_sm_id}",
        )

    # === Resolver Methods ===

    def resolve_aas_href(
        self,
        aas_id: str,
        *,
        interface: str | None = None,
        protocol: str | None = None,
    ) -> str | None:
        """Resolve the endpoint URL for an AAS.

        Fetches the descriptor and uses the resolver to select the best endpoint.

        Args:
            aas_id: The AAS identifier
            interface: Override preferred interface (e.g., "AAS-3.0")
            protocol: Override preferred protocol (e.g., "HTTPS")

        Returns:
            The endpoint URL, or None if no suitable endpoint found
        """
        descriptor = self.get_shell_descriptor(aas_id)
        config = self._get_resolver_config(interface, protocol)
        return resolve_endpoint(descriptor.endpoints, config)

    def resolve_submodel_href(
        self,
        submodel_id: str,
        *,
        interface: str | None = None,
        protocol: str | None = None,
    ) -> str | None:
        """Resolve the endpoint URL for a Submodel."""
        descriptor = self.get_submodel_descriptor(submodel_id)
        config = self._get_resolver_config(interface, protocol)
        return resolve_endpoint(descriptor.endpoints, config)

    def _get_resolver_config(self, interface: str | None, protocol: str | None) -> ResolverConfig:
        """Build resolver config, merging overrides with defaults."""
        return ResolverConfig(
            preferred_interface=interface or self._resolver_config.preferred_interface,
            preferred_protocol=protocol or self._resolver_config.preferred_protocol,
            fallback_to_any=self._resolver_config.fallback_to_any,
        )

    @staticmethod
    def _extract_cursor(data: dict[str, Any]) -> str | None:
        """Safely extract pagination cursor from response data."""
        paging = data.get("paging_metadata") or data.get("pagingMetadata")
        if paging is None:
            return None
        return paging.get("cursor")  # type: ignore[no-any-return]

    # === Resource Management ===

    def close(self) -> None:
        """Close the underlying HTTP transport."""
        self._transport.close()

    def __enter__(self) -> RegistryClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
