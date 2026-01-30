# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Python client library for AAS Registry APIs (IDTA-01002 Part 2, v3.x).

This package provides a client for interacting with AAS Registry APIs
as defined in IDTA-01002 Part 2, v3.x.

Example:
    >>> from basyx_registry_client import RegistryClient
    >>> client = RegistryClient("http://localhost:8082/api/v3.0")
    >>> for descriptor in client.iter_shell_descriptors():
    ...     print(descriptor.id)
"""

from basyx_registry_client._version import __version__
from basyx_registry_client.async_client import AsyncRegistryClient
from basyx_registry_client.client import RegistryClient
from basyx_registry_client.encoding import base64url_decode, base64url_encode
from basyx_registry_client.exceptions import (
    ConflictError,
    NotFoundError,
    RegistryAPIError,
    RegistryConnectionError,
    RegistryError,
    ValidationError,
)
from basyx_registry_client.http import AsyncHTTPTransport, HTTPTransport
from basyx_registry_client.integrations.basyx_client import aas_client_from_registry
from basyx_registry_client.models import (
    AssetAdministrationShellDescriptor,
    Endpoint,
    ProtocolInformation,
    ServiceDescription,
    SubmodelDescriptor,
)
from basyx_registry_client.pagination import PagedResult
from basyx_registry_client.resolver import ResolverConfig, resolve_endpoint

__all__ = [
    # Version
    "__version__",
    # Clients (main API)
    "RegistryClient",
    "AsyncRegistryClient",
    # Models
    "AssetAdministrationShellDescriptor",
    "SubmodelDescriptor",
    "Endpoint",
    "ProtocolInformation",
    "ServiceDescription",
    # Pagination
    "PagedResult",
    # Resolver
    "ResolverConfig",
    "resolve_endpoint",
    # Exceptions
    "RegistryError",
    "RegistryConnectionError",
    "RegistryAPIError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    # Encoding utilities
    "base64url_encode",
    "base64url_decode",
    # HTTP Transports (advanced usage)
    "HTTPTransport",
    "AsyncHTTPTransport",
    # Integrations
    "aas_client_from_registry",
]
