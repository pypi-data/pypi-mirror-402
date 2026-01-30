# basyx-registry-client

Python client library for AAS Registry APIs (IDTA-01002 Part 2, v3.x).

This library enables service discovery via AAS Registry APIs, allowing you to resolve Asset Administration Shell identifiers to their endpoint URLs. It complements the `basyx-client` repository client by providing the registry lookup layer in the workflow: `ID → Registry → Endpoint → AASClient → Data`.

## Installation

```bash
pip install basyx-registry-client
```

With optional basyx-client integration:

```bash
pip install basyx-registry-client[basyx]
```

For development:

```bash
pip install basyx-registry-client[dev]
```

## Quickstart

```python
from basyx_registry_client import AsyncRegistryClient, RegistryClient

# Create a registry client
client = RegistryClient(base_url="https://registry.example.com/api/v3.0")

# List all shell descriptors
for descriptor in client.iter_shell_descriptors():
    print(f"AAS: {descriptor.id}")

# Resolve an AAS endpoint by its identifier
aas_id = "https://example.com/aas/motor-001"
endpoint = client.resolve_aas_href(aas_id)
print(f"Endpoint URL: {endpoint}")

# Optional filters
page = client.list_shell_descriptors(id_short="Motor001", asset_kind="Instance")
print(f"Filtered page size: {len(page)}")

# Async usage
async with AsyncRegistryClient(base_url="https://registry.example.com/api/v3.0") as client:
    descriptor = await client.get_shell_descriptor(aas_id)
    print(f"Found: {descriptor.id_short}")
```

With basyx-client integration:

```python
from basyx_registry_client import RegistryClient
from basyx_registry_client.integrations import aas_client_from_registry

registry = RegistryClient("https://registry.example.com/api/v3.0")
aas = aas_client_from_registry(registry, "urn:example:aas:1")
shell = aas.get_shell("urn:example:aas:1")
```

## Features

- Synchronous and asynchronous API support
- Full type annotations with Pydantic models
- Compliant with IDTA-01002 Part 2, v3.x specification
- Shell and submodel descriptor CRUD operations
- Optional idShort/assetKind filters for shell descriptor listings
- Resolve identifiers to preferred endpoints

## API Reference

*Documentation coming soon.*

## License

Apache-2.0
