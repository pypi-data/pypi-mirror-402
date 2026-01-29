"""Basic usage example - loading and querying SCP manifests and graphs."""

from scp_sdk import Manifest, Graph


def main():
    print("=== SCP SDK Basic Usage Example ===\n")

    # Example 1: Load and query a manifest
    print("1. Loading manifest from YAML string...")
    yaml_content = """
scp: "0.1.0"

system:
  urn: "urn:scp:payment-service"
  name: "Payment Service"
  classification:
    tier: 1
    domain: "payments"

ownership:
  team: "payments-platform"
  contacts:
    - type: "slack"
      ref: "#team-payments"

provides:
  - capability: "payment-processing"
    type: "rest"

depends:
  - system: "urn:scp:user-service"
    type: "rest"
    criticality: "required"
    failure_mode: "fail-fast"
"""

    manifest = Manifest.from_yaml(yaml_content)
    print(f"   URN: {manifest.urn}")
    print(f"   Name: {manifest.name}")
    print(f"   Tier: {manifest.tier}")
    print(f"   Team: {manifest.team}")
    print(f"   Capabilities: {[c.capability for c in manifest.capabilities]}")
    print(f"   Dependencies: {len(manifest.dependencies)}")

    # Query a specific dependency
    dep = manifest.get_dependency("urn:scp:user-service")
    if dep:
        print("\n   Dependency on user-service:")
        print(f"     Type: {dep.type}")
        print(f"     Criticality: {dep.criticality}")
        print(f"     Failure Mode: {dep.failure_mode}")

    # Validation
    result = manifest.validate()
    print(f"\n   Validation: {'✓ Valid' if result.valid else '✗ Invalid'}")

    # Example 2: Build and query a graph
    print("\n2. Building graph from manifests...")

    # Create a second manifest
    yaml_content_2 = """
scp: "0.1.0"

system:
  urn: "urn:scp:user-service"
  name: "User Service"
  classification:
    tier: 1
    domain: "identity"

ownership:
  team: "identity-platform"

provides:
  - capability: "user-management"
    type: "rest"
"""

    manifest2 = Manifest.from_yaml(yaml_content_2)

    # Build graph
    graph = Graph.from_manifests([manifest, manifest2])
    print(f"   Graph contains {len(graph)} systems")

    # Query systems
    print("\n   Systems:")
    for system in graph.systems():
        print(f"     - {system.name} ({system.urn})")

    # Query dependencies
    payment_system = graph.find_system("urn:scp:payment-service")
    if payment_system:
        deps = graph.dependencies_of(payment_system)
        print(f"\n   {payment_system.name} depends on {len(deps)} systems:")
        for edge in deps:
            to_system = graph.find_system(edge.to_urn)
            if to_system:
                print(f"     - {to_system.name} ({edge.criticality})")

    # Blast radius (who depends on user-service)
    user_system = graph.find_system("urn:scp:user-service")
    if user_system:
        dependents = graph.dependents_of(user_system)
        print(f"\n   Systems depending on {user_system.name}: {len(dependents)}")
        for edge in dependents:
            from_system = graph.find_system(edge.from_urn)
            if from_system:
                print(f"     - {from_system.name}")

    # Example 3: Export graph to JSON
    print("\n3. Exporting graph to JSON format...")
    graph_dict = graph.to_dict()
    print(f"   Nodes: {len(graph_dict['nodes'])}")
    print(f"   Edges: {len(graph_dict['edges'])}")

    print("\n✓ Example complete!")


if __name__ == "__main__":
    main()
