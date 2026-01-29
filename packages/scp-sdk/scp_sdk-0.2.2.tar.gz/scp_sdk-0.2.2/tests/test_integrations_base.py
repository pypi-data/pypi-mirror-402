"""Tests for integration base classes."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from scp_sdk import (
    IntegrationConfig,
    IntegrationResult,
    IntegrationValidator,
    Graph,
    SystemNode,
    ValidationIssue,
)


class TestIntegrationConfig:
    """Tests for IntegrationConfig base class."""

    def test_default_instance(self):
        """Should create default instance when no config file exists."""
        config = IntegrationConfig.load()
        assert isinstance(config, IntegrationConfig)

    def test_explicit_path_not_found(self):
        """Should raise FileNotFoundError for explicit non-existent path."""
        with pytest.raises(FileNotFoundError):
            IntegrationConfig.load(Path("/nonexistent/config.yaml"))

    def test_load_from_file(self):
        """Should load config from YAML file."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("# Empty config\n")

            config = IntegrationConfig.load(config_path)
            assert isinstance(config, IntegrationConfig)

    def test_subclass_with_fields(self):
        """Should work with subclasses that have fields."""

        class MyConfig(IntegrationConfig):
            api_key: str = "default"
            endpoint: str = "https://api.example.com"

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(
                "api_key: secret123\nendpoint: https://prod.example.com\n"
            )

            config = MyConfig.load(config_path)
            assert config.api_key == "secret123"
            assert config.endpoint == "https://prod.example.com"

    def test_to_yaml(self):
        """Should export config to YAML string."""

        class MyConfig(IntegrationConfig):
            api_key: str = "test"

        config = MyConfig()
        yaml_str = config.to_yaml()
        assert "api_key: test" in yaml_str


class TestIntegrationResult:
    """Tests for IntegrationResult class."""

    def test_default_values(self):
        """Should have correct default values."""
        result = IntegrationResult()
        assert result.success is True
        assert result.items_processed == 0
        assert result.items_failed == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error(self):
        """Should add error and update state."""
        result = IntegrationResult()
        result.add_error(system="urn:scp:test:foo", message="Failed to sync")

        assert len(result.errors) == 1
        assert result.errors[0]["system"] == "urn:scp:test:foo"
        assert result.items_failed == 1
        assert result.success is False

    def test_add_warning(self):
        """Should add warning without affecting success."""
        result = IntegrationResult()
        result.add_warning(message="Deprecated field used")

        assert len(result.warnings) == 1
        assert result.warnings[0]["message"] == "Deprecated field used"
        assert result.success is True  # Warnings don't affect success

    def test_multiple_errors(self):
        """Should accumulate multiple errors."""
        result = IntegrationResult()
        result.add_error(system="foo")
        result.add_error(system="bar")

        assert len(result.errors) == 2
        assert result.items_failed == 2


class TestIntegrationValidator:
    """Tests for IntegrationValidator base class."""

    def test_abstract_enforcement(self):
        """Should enforce implementation of abstract methods."""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            IntegrationValidator()

    def test_concrete_implementation(self):
        """Should allow concrete implementations."""

        class MyValidator(IntegrationValidator):
            def validate_system(self, system):
                issues = []
                if not system.name:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="MISSING_NAME",
                            message="Name required",
                        )
                    )
                return issues

            def validate_graph(self, graph):
                return graph.validate()

        validator = MyValidator()
        assert isinstance(validator, IntegrationValidator)

        # Test system validation
        system = SystemNode(urn="urn:scp:test:foo", name="")
        issues = validator.validate_system(system)
        assert len(issues) == 1
        assert issues[0].code == "MISSING_NAME"

        # Test graph validation
        graph = Graph(systems=[], edges=[])
        issues = validator.validate_graph(graph)
        assert isinstance(issues, list)
