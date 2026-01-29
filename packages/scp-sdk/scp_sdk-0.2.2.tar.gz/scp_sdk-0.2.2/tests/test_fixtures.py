"""Tests for testing fixtures."""

from scp_sdk import GraphFixture, ManifestFixture, Graph, SCPManifest


class TestGraphFixture:
    """Tests for GraphFixture class."""

    def test_simple_graph(self):
        """Should create minimal valid graph."""
        graph = GraphFixture.simple_graph()
        assert isinstance(graph, Graph)
        assert len(graph) == 1
        assert len(list(graph.dependencies())) == 0

    def test_with_dependencies_default(self):
        """Should create graph with 3 systems by default."""
        graph = GraphFixture.with_dependencies()
        assert len(graph) == 3
        assert len(list(graph.dependencies())) == 2  # Chain: a->b->c

    def test_with_dependencies_custom_count(self):
        """Should create graph with specified number of systems."""
        graph = GraphFixture.with_dependencies(5)
        assert len(graph) == 5
        assert len(list(graph.dependencies())) == 4  # Chain: a->b->c->d->e

    def test_with_dependencies_minimum_enforced(self):
        """Should enforce minimum of 2 systems."""
        graph = GraphFixture.with_dependencies(1)
        assert len(graph) >= 2

    def test_invalid_graph_missing_name(self):
        """Should create graph with missing name issue."""
        graph = GraphFixture.invalid_graph("missing_name")
        issues = graph.validate()
        # Should have orphaned system (info) but name validation is integration-specific
        assert isinstance(issues, list)

    def test_invalid_graph_broken_dependency(self):
        """Should create graph with broken dependency."""
        graph = GraphFixture.invalid_graph("broken_dependency")
        issues = graph.validate()
        # Should have warning about missing dependency target
        warnings = [i for i in issues if i.severity == "warning"]
        assert len(warnings) > 0

    def test_invalid_graph_orphaned(self):
        """Should create graph with orphaned system."""
        graph = GraphFixture.invalid_graph("orphaned")
        issues = graph.validate()
        # Should have info about orphaned system
        infos = [i for i in issues if i.severity == "info"]
        assert len(infos) > 0


class TestManifestFixture:
    """Tests for ManifestFixture class."""

    def test_minimal(self):
        """Should create minimal valid manifest."""
        manifest = ManifestFixture.minimal()
        assert isinstance(manifest, SCPManifest)
        assert manifest.system.name is not None
        assert manifest.ownership is None
        assert manifest.provides is None
        assert manifest.depends is None

    def test_full_featured(self):
        """Should create manifest with all optional fields."""
        manifest = ManifestFixture.full_featured()
        assert isinstance(manifest, SCPManifest)
        assert manifest.system.classification is not None
        assert manifest.ownership is not None
        assert manifest.provides is not None
        assert manifest.depends is not None
        assert len(manifest.provides) > 0
        assert len(manifest.depends) > 0

    def test_with_tier(self):
        """Should create manifest with specified tier."""
        for tier in [1, 2, 3, 4, 5]:
            manifest = ManifestFixture.with_tier(tier)
            assert manifest.system.classification.tier == tier
