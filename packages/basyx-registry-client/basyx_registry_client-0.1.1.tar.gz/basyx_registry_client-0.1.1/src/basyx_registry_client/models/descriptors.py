# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Descriptor models for AAS Registry API.

Per IDTA-01002 Part 2, these models represent the descriptors for Asset Administration
Shells and Submodels registered in the registry.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from basyx_registry_client.models.endpoints import Endpoint


class SubmodelDescriptor(BaseModel):
    """Descriptor for a Submodel registered in the registry.

    The id field is the unique identifier (IRI) of the Submodel.
    This descriptor provides metadata and endpoint information for accessing
    the actual Submodel.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., description="Unique identifier (IRI) of the Submodel")
    id_short: str | None = Field(
        None,
        alias="idShort",
        description="Short identifier of the Submodel",
    )
    semantic_id: dict[str, Any] | None = Field(
        None,
        alias="semanticId",
        description="Semantic identifier reference",
    )
    supplemental_semantic_id: list[dict[str, Any]] | None = Field(
        None,
        alias="supplementalSemanticId",
        description="Additional semantic identifiers",
    )
    administration: dict[str, Any] | None = Field(
        None,
        description="Administrative information (version, revision)",
    )
    description: list[dict[str, Any]] | None = Field(
        None,
        description="Multi-language description (LangStringSet)",
    )
    display_name: list[dict[str, Any]] | None = Field(
        None,
        alias="displayName",
        description="Multi-language display name (LangStringSet)",
    )
    extensions: list[dict[str, Any]] | None = Field(
        None,
        description="Custom extensions",
    )
    endpoints: list[Endpoint] = Field(
        default_factory=list,
        description="Endpoints for accessing the Submodel",
    )


class AssetAdministrationShellDescriptor(BaseModel):
    """Descriptor for an AAS registered in the registry.

    The id field is the unique identifier (IRI) of the AAS.
    This descriptor provides metadata, asset information, and endpoint
    information for accessing the actual AAS.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., description="Unique identifier (IRI) of the AAS")
    id_short: str | None = Field(
        None,
        alias="idShort",
        description="Short identifier of the AAS",
    )
    asset_kind: str | None = Field(
        None,
        alias="assetKind",
        description="Kind of asset: 'Instance' or 'Type'",
    )
    asset_type: str | None = Field(
        None,
        alias="assetType",
        description="Type of the asset",
    )
    global_asset_id: str | None = Field(
        None,
        alias="globalAssetId",
        description="Global identifier of the asset",
    )
    specific_asset_ids: list[dict[str, Any]] | None = Field(
        None,
        alias="specificAssetIds",
        description="Specific asset identifiers (SpecificAssetId[])",
    )
    administration: dict[str, Any] | None = Field(
        None,
        description="Administrative information (version, revision)",
    )
    description: list[dict[str, Any]] | None = Field(
        None,
        description="Multi-language description (LangStringSet)",
    )
    display_name: list[dict[str, Any]] | None = Field(
        None,
        alias="displayName",
        description="Multi-language display name (LangStringSet)",
    )
    extensions: list[dict[str, Any]] | None = Field(
        None,
        description="Custom extensions",
    )
    endpoints: list[Endpoint] = Field(
        default_factory=list,
        description="Endpoints for accessing the AAS",
    )
    submodel_descriptors: list[SubmodelDescriptor] | None = Field(
        None,
        alias="submodelDescriptors",
        description="Descriptors for Submodels contained in this AAS",
    )
