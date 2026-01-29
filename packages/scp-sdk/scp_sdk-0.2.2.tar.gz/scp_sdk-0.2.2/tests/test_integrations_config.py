"""Tests for integrations config module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from scp_sdk.integrations.config import (
    AuthConfig,
    IntegrationConfig,
    substitute_env_vars,
    load_config,
)


class TestAuthConfig:
    """Tests for AuthConfig model."""

    def test_create_with_api_key(self):
        """Should create auth config with API key."""
        auth = AuthConfig(api_key="test123")
        assert auth.api_key == "test123"

    def test_create_with_multiple_fields(self):
        """Should support multiple auth fields."""
        auth = AuthConfig(
            username="user", password="pass", client_id="id", client_secret="secret"
        )
        assert auth.username == "user"
        assert auth.client_id == "id"


class TestIntegrationConfig:
    """Tests for IntegrationConfig model."""

    def test_create_minimal(self):
        """Should create integration config with minimal fields."""
        config = IntegrationConfig(name="test-integration")
        assert config.name == "test-integration"
        assert config.batch_size == 100  # default
        assert config.timeout_seconds == 30

    def test_create_with_auth(self):
        """Should include auth configuration."""
        auth = AuthConfig(api_key="key123")
        config = IntegrationConfig(name="test", auth=auth)
        assert config.auth.api_key == "key123"


class TestSubstituteEnvVars:
    """Tests for environment variable substitution."""

    def test_substitute_simple_var(self, monkeypatch):
        """Should substitute ${VAR} in string."""
        monkeypatch.setenv("MY_VAR", "my_value")
        result = substitute_env_vars("Value is ${MY_VAR}")
        assert result == "Value is my_value"

    def test_substitute_in_dict(self, monkeypatch):
        """Should substitute in dictionary values."""
        monkeypatch.setenv("API_KEY", "secret123")
        data = {"api_key": "${API_KEY}", "other": "value"}
        result = substitute_env_vars(data)
        assert result["api_key"] == "secret123"
        assert result["other"] == "value"

    def test_substitute_in_list(self, monkeypatch):
        """Should substitute in list items."""
        monkeypatch.setenv("VAR", "replaced")
        data = ["${VAR}", "static"]
        result = substitute_env_vars(data)
        assert result == ["replaced", "static"]

    def test_missing_var_returns_empty(self):
        """Should replace missing vars with empty string."""
        result = substitute_env_vars("${NONEXISTENT_VAR}")
        assert result == ""


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_from_file(self):
        """Should load config from YAML file."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_file.write_text("""
name: test-integration
vendor: TestVendor
batch_size: 50
""")
            config = load_config(config_file)
            assert config.name == "test-integration"
            assert config.vendor == "TestVendor"
            assert config.batch_size == 50

    def test_load_with_env_substitution(self, monkeypatch):
        """Should substitute environment variables."""
        monkeypatch.setenv("INTEGRATION_NAME", "my-integration")

        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_file.write_text("name: ${INTEGRATION_NAME}\n")

            config = load_config(config_file)
            assert config.name == "my-integration"

    def test_load_with_integration_section(self):
        """Should extract integration section."""
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_file.write_text("""
integration:
  name: test
  batch_size: 200
""")
            config = load_config(config_file)
            assert config.name == "test"
            assert config.batch_size == 200

    def test_file_not_found(self):
        """Should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))
