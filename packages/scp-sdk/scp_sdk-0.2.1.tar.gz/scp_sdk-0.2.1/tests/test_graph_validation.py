"""Tests for Graph validation functionality."""

from scp_sdk import Graph, SystemNode, DependencyEdge


class TestGraphValidate:
    """Tests for Graph.validate() method."""

    def test_empty_graph_is_valid(self):
        """Empty graph should be valid."""
        graph = Graph(systems=[], edges=[])
        issues = graph.validate()
        assert len(issues) == 0

    def test_single_system_orphaned(self):
        """Single system with no edges should be flagged as orphaned."""
        system = SystemNode(urn="urn:scp:test:service-a", name="Service A")
        graph = Graph(systems=[system], edges=[])

        issues = graph.validate()

        assert len(issues) == 1
        assert issues[0].severity == "info"
        assert issues[0].code == "ORPHANED_SYSTEM"
        assert "Service A" in issues[0].message

    def test_valid_graph_with_dependencies(self):
        """Valid graph with dependencies should have no errors."""
        system_a = SystemNode(urn="urn:scp:test:service-a", name="Service A")
        system_b = SystemNode(urn="urn:scp:test:service-b", name="Service B")
        edge = DependencyEdge(
            from_urn="urn:scp:test:service-a", to_urn="urn:scp:test:service-b"
        )

        graph = Graph(systems=[system_a, system_b], edges=[edge])
        issues = graph.validate()

        # No errors or warnings, both systems are connected
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        assert len(errors) == 0
        assert len(warnings) == 0

    def test_missing_dependency_target(self):
        """Missing dependency target should be flagged as warning."""
        system_a = SystemNode(urn="urn:scp:test:service-a", name="Service A")
        edge = DependencyEdge(
            from_urn="urn:scp:test:service-a", to_urn="urn:scp:test:missing"
        )

        graph = Graph(systems=[system_a], edges=[edge])
        issues = graph.validate()

        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) == 1
        assert warnings[0].code == "MISSING_DEPENDENCY_TARGET"
        assert "urn:scp:test:missing" in warnings[0].message
        assert warnings[0].context["to_urn"] == "urn:scp:test:missing"
        assert warnings[0].context["from_urn"] == "urn:scp:test:service-a"

    def test_self_dependency(self):
        """Self-referencing dependency should be flagged as warning."""
        system_a = SystemNode(urn="urn:scp:test:service-a", name="Service A")
        edge = DependencyEdge(
            from_urn="urn:scp:test:service-a", to_urn="urn:scp:test:service-a"
        )

        graph = Graph(systems=[system_a], edges=[edge])
        issues = graph.validate()

        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) == 1
        assert warnings[0].code == "SELF_DEPENDENCY"
        assert "depends on itself" in warnings[0].message.lower()

    def test_multiple_issues(self):
        """Graph can have multiple validation issues."""
        system_a = SystemNode(urn="urn:scp:test:service-a", name="Service A")
        system_b = SystemNode(urn="urn:scp:test:service-b", name="Service B")
        system_c = SystemNode(urn="urn:scp:test:service-c", name="Service C")

        # service-a → missing (broken dependency)
        # service-b → service-b (self dependency)
        # service-c (orphaned)
        edges = [
            DependencyEdge(
                from_urn="urn:scp:test:service-a", to_urn="urn:scp:test:missing"
            ),
            DependencyEdge(
                from_urn="urn:scp:test:service-b", to_urn="urn:scp:test:service-b"
            ),
        ]

        graph = Graph(systems=[system_a, system_b, system_c], edges=edges)
        issues = graph.validate()

        # Should have 2 warnings (missing target, self-dep) + 1 info (orphaned)
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        infos = [i for i in issues if i.severity == "info"]

        assert len(errors) == 0
        assert len(warnings) == 2
        assert len(infos) == 1

        # Check specific issues
        codes = {i.code for i in issues}
        assert "MISSING_DEPENDENCY_TARGET" in codes
        assert "SELF_DEPENDENCY" in codes
        assert "ORPHANED_SYSTEM" in codes

    def test_validation_issue_context(self):
        """ValidationIssue context should contain relevant details."""
        system_a = SystemNode(urn="urn:scp:test:service-a", name="Service A")
        edge = DependencyEdge(
            from_urn="urn:scp:test:service-a",
            to_urn="urn:scp:test:missing",
            capability="api",
        )

        graph = Graph(systems=[system_a], edges=[edge])
        issues = graph.validate()

        issue = [i for i in issues if i.code == "MISSING_DEPENDENCY_TARGET"][0]
        assert "from_urn" in issue.context
        assert "to_urn" in issue.context
        assert "capability" in issue.context
        assert issue.context["capability"] == "api"

    def test_external_dependencies_are_warnings(self):
        """External dependencies (missing targets) should be warnings, not errors."""
        system_a = SystemNode(urn="urn:scp:test:service-a", name="Service A")
        edge = DependencyEdge(
            from_urn="urn:scp:test:service-a", to_urn="urn:scp:external:third-party-api"
        )

        graph = Graph(systems=[system_a], edges=[edge])
        issues = graph.validate()

        # Should be warning (might be valid external dependency)
        warnings = [i for i in issues if i.code == "MISSING_DEPENDENCY_TARGET"]
        assert len(warnings) == 1
        assert warnings[0].severity == "warning"
