# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 hadijannat
"""Endpoint and protocol information models for AAS Registry API.

Per IDTA-01002 Part 2, these models describe how to communicate with AAS and Submodel
endpoints registered in the registry.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProtocolInformation(BaseModel):
    """Protocol information for an endpoint.

    Per IDTA-01002, this describes how to communicate with an endpoint,
    including the URL, protocol details, and security attributes.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    href: str = Field(..., description="URL of the endpoint")
    endpoint_protocol: str | None = Field(
        None,
        alias="endpointProtocol",
        description="Protocol used, e.g., 'HTTPS', 'OPC-UA'",
    )
    endpoint_protocol_version: str | None = Field(
        None,
        alias="endpointProtocolVersion",
        description="Version of the protocol",
    )
    subprotocol: str | None = Field(
        None,
        description="Subprotocol used, e.g., 'AAS'",
    )
    subprotocol_body: str | None = Field(
        None,
        alias="subprotocolBody",
        description="Body of the subprotocol request",
    )
    subprotocol_body_encoding: str | None = Field(
        None,
        alias="subprotocolBodyEncoding",
        description="Encoding of the subprotocol body, e.g., 'plain'",
    )
    security_attributes: list[dict[str, str]] | None = Field(
        None,
        alias="securityAttributes",
        description="Security attributes for the endpoint",
    )


class Endpoint(BaseModel):
    """An endpoint description within a descriptor.

    Contains protocol information and interface designation for accessing
    an AAS or Submodel.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    interface: str = Field(
        ...,
        description="Interface type, e.g., 'AAS-3.0', 'SUBMODEL-3.0'",
    )
    protocol_information: ProtocolInformation = Field(
        ...,
        alias="protocolInformation",
        description="Protocol details for this endpoint",
    )
