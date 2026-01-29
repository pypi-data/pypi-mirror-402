"""Test fixtures for SCP SDK testing.

Provides convenient factory methods for creating test graphs and manifests,
reducing boilerplate in integration tests.
"""

from typing import Literal

from ..core.graph import Graph, SystemNode, DependencyEdge
from ..core.models import (
    SCPManifest,
    System,
    Ownership,
    Contact,
    Capability,
    Dependency,
    Classification,
)


class GraphFixture:
    """Factory for test graphs.

    Provides pre-built graph structures for testing graph algorithms and validation.

    Example:
        >>> # Valid simple graph
        >>> graph = GraphFixture.simple_graph()
        >>>
        >>> # Graph with 3 systems in a dependency chain
        >>> graph = GraphFixture.with_dependencies(3)
        >>>
        >>> # Graph with explicit validation issue
        >>> graph = GraphFixture.invalid_graph("broken_dependency")
    """

    @staticmethod
    def simple_graph() -> Graph:
        """Create minimal valid graph for testing.

        Returns:
            Graph with single system, no dependencies
        """
        system = SystemNode(urn="urn:scp:test:service-a", name="Test Service A")
        return Graph(systems=[system], edges=[])

    @staticmethod
    def with_dependencies(num_systems: int = 3) -> Graph:
        """Create graph with dependency edges.

        Creates a chain: system-a -> system-b -> system-c

        Args:
            num_systems: Number of systems to create (minimum 2)

        Returns:
            Graph with systems and dependency edges
        """
        if num_systems < 2:
            num_systems = 2

        systems = []
        edges = []

        for i in range(num_systems):
            urn = f"urn:scp:test:service-{chr(ord('a') + i)}"
            name = f"Test Service {chr(ord('A') + i)}"
            systems.append(SystemNode(urn=urn, name=name, tier=i % 5 + 1))

            # Create edge to next system (except for last)
            if i < num_systems - 1:
                next_urn = f"urn:scp:test:service-{chr(ord('a') + i + 1)}"
                edges.append(DependencyEdge(from_urn=urn, to_urn=next_urn))

        return Graph(systems=systems, edges=edges)

    @staticmethod
    def invalid_graph(
        issue: Literal[
            "missing_name", "broken_dependency", "orphaned"
        ] = "missing_name",
    ) -> Graph:
        """Create graph with specific validation issue.

        Args:
            issue: Type of validation issue to create

        Returns:
            Graph with specified validation issue
        """
        if issue == "missing_name":
            system = SystemNode(urn="urn:scp:test:invalid", name="")
            return Graph(systems=[system], edges=[])

        elif issue == "broken_dependency":
            system = SystemNode(urn="urn:scp:test:service-a", name="Service A")
            edge = DependencyEdge(
                from_urn="urn:scp:test:service-a", to_urn="urn:scp:test:missing"
            )
            return Graph(systems=[system], edges=[edge])

        elif issue == "orphaned":
            system = SystemNode(urn="urn:scp:test:orphan", name="Orphaned System")
            return Graph(systems=[system], edges=[])

        return GraphFixture.simple_graph()


class ManifestFixture:
    """Factory for test manifests.

    Example:
        >>> manifest = ManifestFixture.minimal()
        >>> assert manifest.system.name is not None
        >>>
        >>> manifest = ManifestFixture.full_featured()
        >>> assert manifest.ownership is not None
    """

    @staticmethod
    def minimal() -> SCPManifest:
        """Minimal valid manifest.

        Returns:
            Manifest with only required fields
        """
        return SCPManifest(
            scp="0.1.0",
            system=System(urn="urn:scp:test:minimal", name="Minimal Service"),
        )

    @staticmethod
    def full_featured() -> SCPManifest:
        """Manifest with all optional fields.

        Returns:
            Manifest with classification, ownership, capabilities, dependencies
        """
        return SCPManifest(
            scp="0.1.0",
            system=System(
                urn="urn:scp:test:full",
                name="Full Featured Service",
                description="A test service with all features",
                classification=Classification(
                    tier=2, domain="test", tags=["api", "backend"]
                ),
            ),
            ownership=Ownership(
                team="platform-team",
                contacts=[
                    Contact(type="email", ref="team@example.com"),
                    Contact(type="slack", ref="#platform"),
                ],
                escalation=["lead", "manager", "director"],
            ),
            provides=[
                Capability(capability="user-api", type="rest"),  # type: ignore[call-arg]
                Capability(capability="user-events", type="event"),  # type: ignore[call-arg]
            ],
            depends=[
                Dependency(
                    system="urn:scp:test:database",
                    capability="user-data",
                    type="data",
                    criticality="required",
                    failure_mode="fail-fast",
                )
            ],
        )

    @staticmethod
    def with_tier(tier: int) -> SCPManifest:
        """Create manifest with specific tier.

        Args:
            tier: Tier value (1-5)

        Returns:
            Manifest with specified tier
        """
        return SCPManifest(
            scp="0.1.0",
            system=System(
                urn=f"urn:scp:test:tier-{tier}",
                name=f"Tier {tier} Service",
                classification=Classification(tier=tier),
            ),
        )
