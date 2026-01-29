# SCP SDK API Reference

This document provides a comprehensive reference for the SCP SDK's public API.

## Core Models

The core data models are defined in `scp_sdk.core.models`. These Pydantic models represent the structure of SCP manifests.

### SCPManifest

Root model representing a complete `scp.yaml` file.

```python
from scp_sdk.core.models import SCPManifest

# Properties
urn: str  # System URN, e.g., "urn:scp:payment-service"
name: str # System name
```

### System

Core system identification.

```python
from scp_sdk.core.models import System

system = System(
    urn="urn:scp:payment-service",
    name="Payment Service",
    description="Handles payment processing",
    version="1.0.0"
)
```

**Fields:**

- `urn` (str): Unique Resource Name. Must match `^urn:scp:[a-z0-9-]+(:[a-z0-9-]+)?$`.
- `name` (str): Human-readable name.
- `description` (str | None): Detailed description.
- `version` (str | None): Semantic version.
- `classification` (Classification | None): System metadata (tier, domain).

### Dependency

Represents a dependency on another system.

```python
from scp_sdk.core.models import Dependency, RetryConfig

dep = Dependency(
    system="urn:scp:auth-service",
    criticality="required",
    retry=RetryConfig(max_attempts=3)
)
```

**Fields:**

- `system` (str): URN of the provider system.
- `capability` (str | None): Specific capability being consumed.
- `type` (str): Interaction type (rest, grpc, event, etc.).
- `criticality` (str): Impact of failure ('required', 'degraded', 'optional').
- `failure_mode` (str | None): Expected failure behavior (fail-fast, circuit-break, etc.).
- `timeout_ms` (int | None): Client-side timeout.
- `retry` (RetryConfig | None): Retry policy.
- `circuit_breaker` (CircuitBreakerConfig | None): Circuit breaker settings.

### Capability

Represents a capability provided by the system.

```python
from scp_sdk.core.models import Capability

cap = Capability(
    capability="process-payment",
    type="rest",
    description="Process credit card payments"
)
```

**Fields:**

- `capability` (str): Unique name within the system.
- `type` (str): Protocol type.
- `contract` (Contract | None): API contract reference.
- `sla` (SLA | None): Service Level Agreement.
- `x-security` (SecurityExtension | None): Security metadata.

---

## Graph API

The `Graph` class provides an interface for analyzing system dependencies.

```python
from scp_sdk import Graph, Manifest

# Load from manifests
manifests = [Manifest.from_file("scp.yaml")]
graph = Graph.from_manifests(manifests)

# Or load from export file
graph = Graph.from_file("graph.json")
```

### Graph Methods

#### `find_system(urn: str) -> SystemNode | None`

Find a system node by its URN.

#### `dependencies_of(system: SystemNode | str) -> list[DependencyEdge]`

Get all outbound dependencies (systems that this system depends on).

#### `dependents_of(system: SystemNode | str) -> list[DependencyEdge]`

Get all inbound dependencies (systems that depend on this system). This represents the "blast radius" or impact of a failure.

#### `validate() -> list[ValidationIssue]`

Check the graph for consistency issues like broken links or cycles.

### SystemNode

Simplified view of a system in the graph.

**Fields:**

- `urn`: System URN.
- `name`: System name.
- `tier`: System tier (1-5).
- `domain`: Business domain.
- `team`: Owning team.

### DependencyEdge

Represents a connection between two systems.

**Fields:**

- `from_urn`: Consumer system URN.
- `to_urn`: Provider system URN.
- `criticality`: Dependency criticality.

---

## Export / Import

Functions for working with the unified JSON graph format.

### `export_graph_json(manifests: list[SCPManifest]) -> dict`

Export a list of manifests to the unified graph JSON format. This format is suitable for ingestion by visualization tools or other integrations.

**Structure:**

```json
{
  "nodes": [{"id": "...", "type": "System", ...}],
  "edges": [{"from": "...", "to": "...", "type": "DEPENDS_ON", ...}],
  "meta": {"systems_count": 10, ...}
}
```

### `import_graph_json(data: dict) -> list[SCPManifest]`

Reconstruct `SCPManifest` objects from the graph JSON data. Note that some fidelity may be lost (e.g., specific file paths are not preserved).

---

## Integration Framework

Base classes for building SCP integrations.

### IntegrationConfig

Standard configuration model for all integrations.

**Fields:**

- `name` (str): Integration name.
- `auth` (AuthConfig): Credentials.
- `field_mappings` (dict): Custom field mapping.
- `batch_size` (int): Processing batch size.

### IntegrationBase

Abstract base class for integrations. Subclasses must implement:

- `sync_system(system: SystemNode) -> IntegrationResult`
- `sync_dependency(edge: DependencyEdge) -> IntegrationResult`

---

## Testing Utilities

Helpers for testing SCP-based applications.

### GraphFixture

Factory for creating test graphs.

- `simple_graph()`: Returns a graph with one system.
- `with_dependencies(n)`: Returns a chain of `n` systems.
- `invalid_graph(issue)`: Returns a broken graph for testing validation.

### CLITestHelper

Helper for testing Typer CLI commands.

```python
helper = CLITestHelper(app)
result = helper.run(["sync", "--dry-run"])
helper.assert_success(result)
```

## Utilities

### TierUtils

Utilities for SCP tier classifications (1-5).

- `get_name(tier)`: Convert integer tier to name (Critical, High, etc.).
- `validate_tier(tier)`: Check if an integer is a valid tier.
- `map_tier(tier, mapping)`: Map tier to external system values.
