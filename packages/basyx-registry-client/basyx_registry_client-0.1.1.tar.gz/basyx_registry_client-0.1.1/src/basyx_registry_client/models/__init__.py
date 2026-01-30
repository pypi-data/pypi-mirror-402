# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Pydantic models for AAS Registry API data structures.

These models represent the JSON structures defined in IDTA-01002 Part 2
for Asset Administration Shell Registry APIs.
"""

from basyx_registry_client.models.descriptors import (
    AssetAdministrationShellDescriptor,
    SubmodelDescriptor,
)
from basyx_registry_client.models.endpoints import Endpoint, ProtocolInformation
from basyx_registry_client.models.service import ServiceDescription

__all__ = [
    "ProtocolInformation",
    "Endpoint",
    "SubmodelDescriptor",
    "AssetAdministrationShellDescriptor",
    "ServiceDescription",
]
