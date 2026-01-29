# SCP SDK

Python SDK for the **System Capability Protocol** (SCP) - programmatic access to manifests and graphs, plus a framework for building integrations.

## Features

- **Core Models**: Type-safe Pydantic models for SCP v0.1 manifests
- **Graph Abstraction**: Efficient querying and traversal of system dependencies
- **Integration Framework**: Reusable base classes and utilities for building integrations (60-80% code reduction)
- **Fully Tested**: Comprehensive test suite with pytest

## Documentation

- **[API Reference](docs/api-reference.md)**: Detailed API documentation for all modules.
- **[Integration Guide](docs/integration-guide.md)**: Step-by-step tutorial for building custom integrations.
- **[Examples](docs/examples.md)**: Common usage patterns and code snippets.

## Architecture

The SDK is composed of three main layers:

1.  **Core (`scp_sdk.core`)**: Defines the data models (`SCPManifest`, `System`, `Dependency`) and the `Graph` abstraction for analyzing architecture.
2.  **Integrations (`scp_sdk.integrations`)**: Provides a framework (`IntegrationBase`, `IntegrationConfig`) for syncing SCP data to external tools (PagerDuty, ServiceNow, etc.).
3.  **Utilities (`scp_sdk.utils`)**: Helper functions for tier handling and common tasks.

## Installation

```bash
# Using uv (recommended)
cd /path/to/scp-sdk
uv sync

# Or with pip
pip install -e .
```

## Quick Start

### Load and Query Manifests

```python
from scp_sdk import Manifest

# Load from file
manifest = Manifest.from_file("scp.yaml")

# Or from YAML string
yaml_str = """
scp: "0.1.0"
system:
  urn: "urn:scp:payment-service"
  name: "Payment Service"
  classification:
    tier: 1
"""
manifest = Manifest.from_yaml(yaml_str)

# Query
print(manifest.urn)  # urn:scp:payment-service
print(manifest.tier)  # 1
print(manifest.team)  # team name

# Get specific dependency
dep = manifest.get_dependency("urn:scp:user-service")
print(dep.criticality)  # required
```

### Build and Query Graphs

```python
from scp_sdk import Graph

# Load from unified JSON (from scp-cli scan --export json)
graph = Graph.from_file("graph.json")

# Or build from manifests
graph = Graph.from_manifests([manifest1, manifest2])

# Query
for system in graph.systems():
    print(system.name)

# Find system
payment_svc = graph.find_system("urn:scp:payment-service")

# Get dependencies
deps = graph.dependencies_of(payment_svc)

# Get blast radius (what depends on this system)
dependents = graph.dependents_of(payment_svc)
```

### Build Custom Integrations

The SDK makes building integrations incredibly simple:

```python
from scp_sdk.core.graph import SystemNode, DependencyEdge
from scp_sdk.integrations.base import IntegrationBase
from scp_sdk.integrations.registry import register_integration

@register_integration("pagerduty")
class PagerDutyIntegration(IntegrationBase):
    """Sync SCP systems to PagerDuty services."""

    def sync_system(self, system: SystemNode) -> None:
        """Create/update PagerDuty service."""
        service_data = {
            "name": system.name,
            "description": f"SCP System: {system.urn}",
            "escalation_policy": self.get_policy(system.team),
        }
        # Call PagerDuty API...

    def sync_dependency(self, edge: DependencyEdge) -> None:
        """Sync dependency (optional for PagerDuty)."""
        pass

# Usage
from scp_sdk.integrations.config import IntegrationConfig

config = IntegrationConfig(name="pagerduty", auth={...})
integration = PagerDutyIntegration(config)
result = integration.sync(graph)
```

The SDK handles:

- Graph iteration
- Error handling & retries
- Logging
- Dry-run mode
- ID caching
- Field mapping utilities

## Development

```bash
# Install dependencies
make setup

# Run tests
make test

# Run linter
make lint

# Format code
make format

# Type check
make typecheck

# Run all checks
make check

# Run examples
make examples
```

## Examples

See the [`examples/`](examples/) directory:

- [`basic_usage.py`](examples/basic_usage.py) - Loading and querying manifests/graphs
- [`custom_integration.py`](examples/custom_integration.py) - Building a PagerDuty integration

Run them with:

```bash
uv run python examples/basic_usage.py
uv run python examples/custom_integration.py
```

## Related Projects

- [scp-definition](https://github.com/krackenservices/scp-definition) - SCP specification and JSON schema
- [scp-integrations](https://github.com/krackenservices/scp-integrations) - CLI tools for scanning and exporting
- [scp-viewer](https://github.com/krackenservices/scp-viewer) - Web dashboard for visualizing architectures
- [scp-demo](https://github.com/krackenservices/scp-demo) - Demo project for example models

## License

MIT
