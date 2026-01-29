"""Graph data structure for SCP architecture."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Self
import json

from .manifest import Manifest
from .models import Dependency, ValidationIssue


@dataclass
class SystemNode:
    """A system node in the architecture graph.

    Represents a simplified view of a system optimized for graph traversal and analysis.
    Derived from the richer System model in the manifest.
    """

    urn: str
    name: str
    tier: int | None = None
    domain: str | None = None
    team: str | None = None
    otel_service_name: str | None = None
    capabilities: list[str] | None = None  # List of capability names
    contacts: list[dict] | None = None
    escalation: list[str] | None = None

    @classmethod
    def from_manifest(cls, manifest: Manifest) -> "SystemNode":
        """Create a SystemNode from a Manifest.

        Args:
            manifest: Source manifest

        Returns:
            SystemNode instance
        """
        capabilities = [cap.capability for cap in manifest.capabilities]

        contacts = None
        escalation = None
        if manifest.data.ownership:
            if manifest.data.ownership.contacts:
                contacts = [
                    {"type": c.type, "ref": c.ref}
                    for c in manifest.data.ownership.contacts
                ]
            escalation = manifest.data.ownership.escalation

        return cls(
            urn=manifest.urn,
            name=manifest.name,
            tier=manifest.tier,
            domain=manifest.domain,
            team=manifest.team,
            otel_service_name=manifest.otel_service_name,
            capabilities=capabilities if capabilities else None,
            contacts=contacts,
            escalation=escalation,
        )


@dataclass
class DependencyEdge:
    """A dependency edge in the architecture graph.

    Represents a directed edge from one system (consumer) to another (provider).
    Carries metadata about the relationship like criticality and failure modes.
    """

    from_urn: str
    to_urn: str
    capability: str | None = None
    type: str | None = None
    criticality: str | None = None
    failure_mode: str | None = None
    timeout_ms: int | None = None

    @classmethod
    def from_dependency(cls, from_urn: str, dep: Dependency) -> "DependencyEdge":
        """Create a DependencyEdge from a Dependency.

        Args:
            from_urn: Source system URN
            dep: Dependency object

        Returns:
            DependencyEdge instance
        """
        return cls(
            from_urn=from_urn,
            to_urn=dep.system,
            capability=dep.capability,
            type=dep.type,
            criticality=dep.criticality,
            failure_mode=dep.failure_mode,
            timeout_ms=dep.timeout_ms,
        )


class Graph:
    """Architecture graph built from SCP manifests.

    Provides efficient querying and traversal of system dependencies.
    Supports loading from unified JSON format or building directly from manifests.

    Example:
        >>> # Load from file
        >>> graph = Graph.from_file("graph.json")
        >>>
        >>> # Build from manifests
        >>> manifests = [Manifest.from_file("scp.yaml")]
        >>> graph = Graph.from_manifests(manifests)
        >>>
        >>> # Find a system
        >>> payment = graph.find_system("urn:scp:payment-service")
        >>>
        >>> # Get dependencies (outbound edges)
        >>> deps = graph.dependencies_of(payment)
        >>> for edge in deps:
        >>>     print(f"Depends on {edge.to_urn} ({edge.criticality})")
        >>>
        >>> # Get blast radius (inbound edges)
        >>> dependents = graph.dependents_of(payment)
    """

    def __init__(self, systems: list[SystemNode], edges: list[DependencyEdge]):
        """Initialize graph with systems and edges.

        Args:
            systems: List of system nodes
            edges: List of dependency edges
        """
        self._systems = {s.urn: s for s in systems}
        self._edges = edges

        # Build adjacency lists for fast lookups
        self._outgoing: dict[str, list[DependencyEdge]] = {}
        self._incoming: dict[str, list[DependencyEdge]] = {}

        for edge in edges:
            if edge.from_urn not in self._outgoing:
                self._outgoing[edge.from_urn] = []
            self._outgoing[edge.from_urn].append(edge)

            if edge.to_urn not in self._incoming:
                self._incoming[edge.to_urn] = []
            self._incoming[edge.to_urn].append(edge)

    @classmethod
    def from_file(cls, path: Path | str) -> Self:
        """Load graph from unified JSON format.

        This expects the output format from scp-cli scan --export json.

        Args:
            path: Path to graph JSON file

        Returns:
            Graph instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON format is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Graph file not found: {path}")

        with open(path, "r") as f:
            data = json.load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Load graph from dictionary.

        Args:
            data: Graph data in unified JSON format

        Returns:
            Graph instance

        Raises:
            ValueError: If data format is invalid
        """
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        # Convert nodes to SystemNode objects
        systems = []
        for node in nodes:
            if node.get("type") == "System":
                systems.append(
                    SystemNode(
                        urn=node.get("id", ""),
                        name=node.get("name", ""),
                        tier=node.get("tier"),
                        domain=node.get("domain"),
                        team=node.get("team"),
                        otel_service_name=node.get("otel_service_name"),
                        capabilities=node.get("capabilities"),
                        contacts=node.get("contacts"),
                        escalation=node.get("escalation"),
                    )
                )

        # Convert edges to DependencyEdge objects
        dep_edges = []
        for edge in edges:
            if edge.get("type") == "DEPENDS_ON":
                dep_edges.append(
                    DependencyEdge(
                        from_urn=edge.get("from", ""),
                        to_urn=edge.get("to", ""),
                        capability=edge.get("capability"),
                        type=edge.get("dependency_type"),
                        criticality=edge.get("criticality"),
                        failure_mode=edge.get("failure_mode"),
                        timeout_ms=edge.get("timeout_ms"),
                    )
                )

        return cls(systems, dep_edges)

    @classmethod
    def from_manifests(cls, manifests: list[Manifest]) -> Self:
        """Build graph from a list of manifests.

        Args:
            manifests: List of SCP manifests

        Returns:
            Graph instance
        """
        systems = [SystemNode.from_manifest(m) for m in manifests]

        edges = []
        for manifest in manifests:
            for dep in manifest.dependencies:
                edges.append(DependencyEdge.from_dependency(manifest.urn, dep))

        return cls(systems, edges)

    def systems(self) -> Iterator[SystemNode]:
        """Iterate over all systems.

        Yields:
            SystemNode instances
        """
        yield from self._systems.values()

    def dependencies(self) -> Iterator[DependencyEdge]:
        """Iterate over all dependency edges.

        Yields:
            DependencyEdge instances
        """
        yield from self._edges

    def find_system(self, urn: str) -> SystemNode | None:
        """Find a system by URN.

        Args:
            urn: System URN to search for (e.g., "urn:scp:payment-service")

        Returns:
            SystemNode if found, None otherwise
        """
        return self._systems.get(urn)

    def dependencies_of(self, system: SystemNode | str) -> list[DependencyEdge]:
        """Get outbound dependencies of a system.

        This returns edges where the given system is the CONSUMER (from_urn).

        Args:
            system: SystemNode object or URN string

        Returns:
            List of outbound dependency edges
        """
        urn = system.urn if isinstance(system, SystemNode) else system
        return self._outgoing.get(urn, [])

    def validate(self) -> list[ValidationIssue]:
        """Validate graph structure and relationships.

        Checks for common structural issues:
        - Missing dependency targets (broken edges)
        - Orphaned systems (no incoming or outgoing edges)
        - Self-referencing dependencies

        Note: Duplicate URNs are prevented by Graph construction (dict-based storage).

        Returns:
            List of validation issues (empty if valid)

        Example:
            >>> graph = Graph.from_file("graph.json")
            >>> issues = graph.validate()
            >>> errors = [i for i in issues if i.severity == "error"]
            >>> if errors:
            >>>     print(f"Found {len(errors)} errors")
        """
        issues: list[ValidationIssue] = []

        # Check for broken dependencies (missing targets)
        for edge in self._edges:
            if not self.find_system(edge.to_urn):
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="MISSING_DEPENDENCY_TARGET",
                        message=f"Dependency target not found: {edge.to_urn}",
                        context={
                            "from_urn": edge.from_urn,
                            "to_urn": edge.to_urn,
                            "capability": edge.capability or "",
                        },
                    )
                )

            # Check for self-referencing dependencies
            if edge.from_urn == edge.to_urn:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="SELF_DEPENDENCY",
                        message=f"System depends on itself: {edge.from_urn}",
                        context={"urn": edge.from_urn},
                    )
                )

        # Check for orphaned systems (no edges at all)
        connected_urns = set()
        for edge in self._edges:
            connected_urns.add(edge.from_urn)
            connected_urns.add(edge.to_urn)

        for system in (
            self._systems.values()
        ):  # Changed to .values() to iterate over SystemNode objects
            if system.urn not in connected_urns:
                issues.append(
                    ValidationIssue(
                        severity="info",
                        code="ORPHANED_SYSTEM",
                        message=f"System has no dependencies: {system.name}",
                        context={"urn": system.urn},
                    )
                )

        return issues

    def dependents_of(self, system: SystemNode | str) -> list[DependencyEdge]:
        """Get systems that depend on this system (blast radius).

        This returns edges where the given system is the PROVIDER (to_urn).
        Useful for analyzing impact of a system failure or change.

        Args:
            system: SystemNode object or URN string

        Returns:
            List of inbound dependency edges
        """
        urn = system.urn if isinstance(system, SystemNode) else system
        return self._incoming.get(urn, [])

    def to_dict(self) -> dict:
        """Export graph to unified JSON format.

        Returns:
            Dictionary in unified JSON format
        """
        nodes = []
        for system in self._systems.values():
            node = {
                "id": system.urn,
                "type": "System",
                "name": system.name,
            }
            if system.tier is not None:
                node["tier"] = system.tier  # type: ignore[assignment]
            if system.domain:
                node["domain"] = system.domain  # type: ignore[assignment]
            if system.team:
                node["team"] = system.team  # type: ignore[assignment]
            if system.otel_service_name:
                node["otel_service_name"] = system.otel_service_name  # type: ignore[assignment]
            if system.capabilities:
                node["capabilities"] = system.capabilities  # type: ignore[assignment]
            if system.contacts:
                node["contacts"] = system.contacts  # type: ignore[assignment]
            if system.escalation:
                node["escalation"] = system.escalation  # type: ignore[assignment]

            nodes.append(node)

        edges = []
        for edge in self._edges:
            e = {
                "from": edge.from_urn,
                "to": edge.to_urn,
                "type": "DEPENDS_ON",
            }
            if edge.capability:
                e["capability"] = edge.capability  # type: ignore[assignment]
            if edge.type:
                e["dependency_type"] = edge.type  # type: ignore[assignment]
            if edge.criticality:
                e["criticality"] = edge.criticality  # type: ignore[assignment]
            if edge.failure_mode:
                e["failure_mode"] = edge.failure_mode  # type: ignore[assignment]
            if edge.timeout_ms is not None:
                e["timeout_ms"] = edge.timeout_ms  # type: ignore[assignment]

            edges.append(e)

        return {"nodes": nodes, "edges": edges}

    def to_json(self, path: Path | str) -> None:
        """Export graph to JSON file.

        Args:
            path: Output path
        """
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def __len__(self) -> int:
        """Get number of systems in graph."""
        return len(self._systems)

    def __repr__(self) -> str:
        return f"Graph(systems={len(self._systems)}, edges={len(self._edges)})"
