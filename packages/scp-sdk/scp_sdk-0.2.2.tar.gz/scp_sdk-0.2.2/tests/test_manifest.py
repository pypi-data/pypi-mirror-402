"""Test Manifest class."""

from scp_sdk.core.manifest import Manifest


def test_manifest_from_yaml():
    """Test loading manifest from YAML string."""
    yaml_str = """
scp: "0.1.0"

system:
  urn: "urn:scp:test-service"
  name: "Test Service"
  classification:
    tier: 2

ownership:
  team: "test-team"
"""
    manifest = Manifest.from_yaml(yaml_str)

    assert manifest.urn == "urn:scp:test-service"
    assert manifest.name == "Test Service"
    assert manifest.tier == 2
    assert manifest.team == "test-team"


def test_manifest_properties():
    """Test manifest convenience properties."""
    yaml_str = """
scp: "0.1.0"

system:
  urn: "urn:scp:payment-service"
  name: "Payment Service"
  classification:
    tier: 1
    domain: "payments"

ownership:
  team: "payments-team"

provides:
  - capability: "payment-processing"
    type: "rest"

depends:
  - system: "urn:scp:user-service"
    type: "rest"
    criticality: "required"
"""
    manifest = Manifest.from_yaml(yaml_str)

    assert manifest.urn == "urn:scp:payment-service"
    assert manifest.name == "Payment Service"
    assert manifest.tier == 1
    assert manifest.domain == "payments"
    assert manifest.team == "payments-team"
    assert len(manifest.capabilities) == 1
    assert len(manifest.dependencies) == 1


def test_get_dependency():
    """Test querying dependencies."""
    yaml_str = """
scp: "0.1.0"

system:
  urn: "urn:scp:test-service"
  name: "Test"

depends:
  - system: "urn:scp:db"
    type: "data"
    criticality: "required"
  - system: "urn:scp:cache"
    type: "data"
    criticality: "optional"
"""
    manifest = Manifest.from_yaml(yaml_str)

    db_dep = manifest.get_dependency("urn:scp:db")
    assert db_dep is not None
    assert db_dep.criticality == "required"

    cache_dep = manifest.get_dependency("urn:scp:cache")
    assert cache_dep is not None
    assert cache_dep.criticality == "optional"

    # Non-existent
    missing = manifest.get_dependency("urn:scp:missing")
    assert missing is None


def test_get_capability():
    """Test querying capabilities."""
    yaml_str = """
scp: "0.1.0"

system:
  urn: "urn:scp:test-service"
  name: "Test"

provides:
  - capability: "api"
    type: "rest"
  - capability: "events"
    type: "event"
"""
    manifest = Manifest.from_yaml(yaml_str)

    api_cap = manifest.get_capability("api")
    assert api_cap is not None
    assert api_cap.type == "rest"

    # Non-existent
    missing = manifest.get_capability("missing")
    assert missing is None


def test_validation():
    """Test manifest validation."""
    # Valid manifest
    valid_yaml = """
scp: "0.1.0"

system:
  urn: "urn:scp:test"
  name: "Test"
"""
    manifest = Manifest.from_yaml(valid_yaml)
    result = manifest.validate()
    assert result.valid is True
    assert len(result.errors) == 0


def test_to_yaml():
    """Test exporting to YAML."""
    yaml_str = """
scp: "0.1.0"

system:
  urn: "urn:scp:test"
  name: "Test"
  classification:
    tier: 1

ownership:
  team: "test-team"
"""
    manifest = Manifest.from_yaml(yaml_str)
    exported_yaml = manifest.to_yaml()

    # Should be able to reload
    manifest2 = Manifest.from_yaml(exported_yaml)
    assert manifest2.urn == manifest.urn
    assert manifest2.name == manifest.name
    assert manifest2.tier == manifest.tier
    assert manifest2.team == manifest.team


def test_to_dict():
    """Test exporting to dictionary."""
    yaml_str = """
scp: "0.1.0"

system:
  urn: "urn:scp:test"
  name: "Test"
"""
    manifest = Manifest.from_yaml(yaml_str)
    data = manifest.to_dict()

    assert data["scp"] == "0.1.0"
    assert data["system"]["urn"] == "urn:scp:test"
    assert data["system"]["name"] == "Test"
