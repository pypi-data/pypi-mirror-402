# SCP SDK Examples

Common patterns and examples for using the SCP SDK.

## Loading a Manifest

Load a single `scp.yaml` file into a python object.

```python
from scp_sdk import Manifest

# Check if file is valid manifest first
try:
    manifest = Manifest.from_file("scp.yaml")
    print(f"Loaded system: {manifest.name} ({manifest.urn})")
except Exception as e:
    print(f"Invalid manifest: {e}")
```

## Traversing the Graph

Load multiple manifests and build an architecture graph.

```python
from pathlib import Path
from scp_sdk import Manifest, Graph

# 1. Load all manifests in directory
manifests = []
for path in Path("./services").rglob("scp.yaml"):
    manifests.append(Manifest.from_file(path))

# 2. Build graph
graph = Graph.from_manifests(manifests)
print(f"Graph built with {len(graph)} systems")

# 3. Find specific system
payment = graph.find_system("urn:scp:payment-service")

if payment:
    # 4. List dependencies (Outbound)
    print("\nDependencies:")
    for edge in graph.dependencies_of(payment):
        print(f"- Depends on {edge.to_urn} ({edge.criticality})")

    # 5. List dependents (Inbound / "Blast Radius")
    print("\nDependents (Blast Radius):")
    for edge in graph.dependents_of(payment):
        print(f"- Used by {edge.from_urn}")
```

## Validating the Architecture

Check for missing dependencies or other structural issues.

```python
from scp_sdk import Graph

graph = Graph.from_file("graph.json")
issues = graph.validate()

errors = [i for i in issues if i.severity == "error"]
warnings = [i for i in issues if i.severity == "warning"]

if errors:
    print(f"Found {len(errors)} errors!")
    for err in errors:
        print(f"[ERROR] {err.message} ({err.code})")

if warnings:
    print(f"Found {len(warnings)} warnings.")
```

## Exporting for Visualization

Export the graph to JSON for use with visualization tools.

```python
from scp_sdk import Graph, export_graph_json
import json

# ... build graph ...

# Export to dictionary
graph_data = graph.to_dict()

# Save to file
graph.to_json("architecture.json")
```

## Creating a Manifest Programmatically

You can create manifests in code, which is useful for migration scripts.

```python
from scp_sdk.core.models import SCPManifest, System, Classification

manifest = SCPManifest(
    scp="0.1.0",
    system=System(
        urn="urn:scp:generated-service",
        name="Generated Service",
        classification=Classification(tier=2, domain="generated")
    )
)

print(manifest.to_yaml())
```
