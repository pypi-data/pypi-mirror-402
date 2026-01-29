"""Test Graph class."""

from scp_sdk.core.graph import Graph, SystemNode, DependencyEdge
from scp_sdk.core.manifest import Manifest


def test_graph_from_manifests():
    """Test building graph from manifests."""
    yaml1 = """
scp: "0.1.0"
system:
  urn: "urn:scp:service-a"
  name: "Service A"
depends:
  - system: "urn:scp:service-b"
    type: "rest"
    criticality: "required"
"""

    yaml2 = """
scp: "0.1.0"
system:
  urn: "urn:scp:service-b"
  name: "Service B"
"""

    m1 = Manifest.from_yaml(yaml1)
    m2 = Manifest.from_yaml(yaml2)

    graph = Graph.from_manifests([m1, m2])

    assert len(graph) == 2
    assert len(list(graph.systems())) == 2
    assert len(list(graph.dependencies())) == 1


def test_graph_from_dict():
    """Test loading graph from unified JSON."""
    data = {
        "nodes": [
            {
                "id": "urn:scp:svc1",
                "type": "System",
                "name": "Service 1",
                "tier": 1,
                "team": "team1",
            },
            {
                "id": "urn:scp:svc2",
                "type": "System",
                "name": "Service 2",
                "tier": 2,
            },
        ],
        "edges": [
            {
                "from": "urn:scp:svc1",
                "to": "urn:scp:svc2",
                "type": "DEPENDS_ON",
                "criticality": "required",
            }
        ],
    }

    graph = Graph.from_dict(data)

    assert len(graph) == 2
    assert len(list(graph.dependencies())) == 1


def test_find_system():
    """Test finding systems by URN."""
    systems = [
        SystemNode(urn="urn:scp:a", name="A"),
        SystemNode(urn="urn:scp:b", name="B"),
    ]
    graph = Graph(systems=systems, edges=[])

    found = graph.find_system("urn:scp:a")
    assert found is not None
    assert found.name == "A"

    missing = graph.find_system("urn:scp:missing")
    assert missing is None


def test_dependencies_of():
    """Test querying outbound dependencies."""
    systems = [
        SystemNode(urn="urn:scp:a", name="A"),
        SystemNode(urn="urn:scp:b", name="B"),
        SystemNode(urn="scp:c", name="C"),
    ]

    edges = [
        DependencyEdge(
            from_urn="urn:scp:a", to_urn="urn:scp:b", criticality="required"
        ),
        DependencyEdge(
            from_urn="urn:scp:a", to_urn="urn:scp:c", criticality="optional"
        ),
    ]

    graph = Graph(systems=systems, edges=edges)

    # Query by SystemNode
    a = graph.find_system("urn:scp:a")
    deps = graph.dependencies_of(a)
    assert len(deps) == 2

    # Query by URN string
    deps = graph.dependencies_of("urn:scp:a")
    assert len(deps) == 2

    # System with no dependencies
    deps = graph.dependencies_of("urn:scp:b")
    assert len(deps) == 0


def test_dependents_of():
    """Test querying inbound dependencies (blast radius)."""
    systems = [
        SystemNode(urn="urn:scp:a", name="A"),
        SystemNode(urn="urn:scp:b", name="B"),
        SystemNode(urn="urn:scp:c", name="C"),
    ]

    edges = [
        DependencyEdge(
            from_urn="urn:scp:a", to_urn="urn:scp:c", criticality="required"
        ),
        DependencyEdge(
            from_urn="urn:scp:b", to_urn="urn:scp:c", criticality="required"
        ),
    ]

    graph = Graph(systems=systems, edges=edges)

    # C is depended on by A and B
    dependents = graph.dependents_of("urn:scp:c")
    assert len(dependents) == 2

    # A has no dependents
    dependents = graph.dependents_of("urn:scp:a")
    assert len(dependents) == 0


def test_to_dict():
    """Test exporting graph to dictionary."""
    systems = [
        SystemNode(urn="urn:scp:a", name="A", tier=1, team="team-a"),
    ]

    edges = [
        DependencyEdge(
            from_urn="urn:scp:a", to_urn="urn:scp:b", criticality="required"
        ),
    ]

    graph = Graph(systems=systems, edges=edges)
    data = graph.to_dict()

    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 1
    assert len(data["edges"]) == 1

    # Check node structure
    node = data["nodes"][0]
    assert node["id"] == "urn:scp:a"
    assert node["name"] == "A"
    assert node["tier"] == 1
    assert node["team"] == "team-a"

    # Check edge structure
    edge = data["edges"][0]
    assert edge["from"] == "urn:scp:a"
    assert edge["to"] == "urn:scp:b"
    assert edge["type"] == "DEPENDS_ON"
