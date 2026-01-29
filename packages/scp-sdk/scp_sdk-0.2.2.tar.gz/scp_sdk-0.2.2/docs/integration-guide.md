# Building SCP Integrations

This guide walks you through the process of creating a new integration for the **System Capability Protocol (SCP)** using the `scp-sdk`.

Integrations allow you to sync your SCP architecture graph with external tools like PagerDuty, ServiceNow, Backstage, or OpsGenie.

## Overview

An integration consists of three main parts:

1. **Registration**: A class decorated with `@register_integration`.
2. **Configuration**: A configuration model inheriting from `IntegrationConfig`.
3. **Implementation**: A class inheriting from `IntegrationBase` that implements `sync_system` and `sync_dependency`.

## Step 1: Create the Integration Class

Create a new file for your integration (e.g., `my_integration.py`).

```python
from typing import Any
from scp_sdk.integrations.base import IntegrationBase, IntegrationResult
from scp_sdk.integrations.registry import register_integration
from scp_sdk.core.graph import SystemNode, DependencyEdge

@register_integration("my-tool")
class MyToolIntegration(IntegrationBase):
    """Integration for My Tool."""

    def sync_system(self, system: SystemNode) -> IntegrationResult:
        # TODO: Implement system sync logic
        return IntegrationResult(status="success", id=system.urn)

    def sync_dependency(self, edge: DependencyEdge) -> IntegrationResult:
        # TODO: Implement dependency sync logic
        return IntegrationResult(status="skipped")
```

## Step 2: Implement System Sync

The `sync_system` method is called for each system in the graph. Your goal is to ensure the system exists in the external tool and is up-to-date.

```python
    def sync_system(self, system: SystemNode) -> IntegrationResult:
        try:
            # 1. Map SCP fields to vendor fields
            payload = {
                "name": system.name,
                "description": f"Managed by SCP. URN: {system.urn}",
                "tier": self._map_tier(system.tier),
            }

            # 2. Call vendor API
            # external_id = self.client.create_or_update_service(payload)
            external_id = "svc-123" # Mocked for example

            return IntegrationResult(
                status="success",
                id=system.urn,
                external_id=external_id
            )

        except Exception as e:
            return IntegrationResult(
                status="error",
                id=system.urn,
                message=str(e)
            )

    def _map_tier(self, tier: int | None) -> str:
        # Map 1-5 scale to vendor specific values
        mapping = {1: "Critical", 2: "High", 3: "Medium"}
        return mapping.get(tier, "Low")
```

## Step 3: Implement Dependency Sync

The `sync_dependency` method is called for each dependency edge.

```python
    def sync_dependency(self, edge: DependencyEdge) -> IntegrationResult:
        # Only sync if criticality is high enough
        if edge.criticality == "optional":
            return IntegrationResult(status="skipped", id=f"{edge.from_urn}->{edge.to_urn}")

        # Logic to create link in external tool
        return IntegrationResult(status="success", id=f"{edge.from_urn}->{edge.to_urn}")
```

## Step 4: Configuration

Users configure your integration via a YAML file. define the options in `IntegrationConfig` if needed, or use the `custom` dictionary.

**config.yaml**:

```yaml
integration:
  name: my-tool
  auth:
    api_key: ${MY_TOOL_API_KEY}
  custom:
    default_priority: P3
```

Access this in your class via `self.config`.

```python
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.api_key = config.auth.api_key
        self.priority = config.custom.get("default_priority", "P3")
```

## Testing Your Integration

Use `scp-sdk.testing.fixtures` to create test data.

```python
from scp_sdk.testing.fixtures import GraphFixture
from my_integration import MyToolIntegration

def test_sync():
    graph = GraphFixture.simple_graph()
    integration = MyToolIntegration(config)

    results = integration.run(graph)
    assert not results.failed
```

## Best Practices

1. **Idempotency**: Your sync methods should be idempotent. Running them multiple times should not create duplicate records.
2. **Error Handling**: Catch exceptions and return `IntegrationResult` with `status="error"`. Do not let one failure crash the entire sync process.
3. **Rate Limiting**: Use `BatchProcessor` from `scp_sdk.integrations.utils` if the API has strict rate limits.
4. **Caching**: Use `IDCache` to cache URN-to-VendorID mappings to reduce API references.
