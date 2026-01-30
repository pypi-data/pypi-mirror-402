# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Service description models for AAS Registry API.

Per IDTA-01002 Part 2, the service description provides information about
the capabilities of the registry server.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ServiceDescription(BaseModel):
    """Response from the /description endpoint.

    Describes the capabilities and supported profiles of the registry server.
    Common profiles include:
    - https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRegistryServiceSpecification/SSP-001
    - https://admin-shell.io/aas/API/3/0/SubmodelRegistryServiceSpecification/SSP-001
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    profiles: list[str] = Field(
        default_factory=list,
        description="List of supported API profiles",
    )
