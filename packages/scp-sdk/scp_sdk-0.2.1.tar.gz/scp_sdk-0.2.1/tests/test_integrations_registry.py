"""Tests for integrations registry module."""

from scp_sdk.integrations.registry import (
    register_integration,
    get_integration,
    list_integrations,
    clear_registry,
)


class TestRegistry:
    """Tests for integration registry functions."""

    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()

    def teardown_method(self):
        """Clear registry after each test."""
        clear_registry()

    def test_register_integration_decorator(self):
        """Should register integration class."""

        @register_integration("test")
        class TestIntegration:
            pass

        assert get_integration("test") == TestIntegration

    def test_get_integration_not_found(self):
        """Should return None for unregistered integration."""
        assert get_integration("nonexistent") is None

    def test_list_integrations(self):
        """Should list all registered integrations."""

        @register_integration("int1")
        class Integration1:
            pass

        @register_integration("int2")
        class Integration2:
            pass

        integrations = list_integrations()
        assert "int1" in integrations
        assert "int2" in integrations
        assert len(integrations) == 2

    def test_clear_registry(self):
        """Should clear all registrations."""

        @register_integration("test")
        class TestIntegration:
            pass

        assert len(list_integrations()) == 1

        clear_registry()

        assert len(list_integrations()) == 0
