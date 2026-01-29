"""High-level Manifest class for loading and manipulating SCP manifests."""

from pathlib import Path
from typing import Self

import yaml
from pydantic import ValidationError

from .models import SCPManifest, Dependency, Capability


class ValidationResult:
    """Result of manifest validation."""

    def __init__(self, valid: bool, errors: list[str] | None = None):
        self.valid = valid
        self.errors = errors or []

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        if self.valid:
            return "ValidationResult(valid=True)"
        return f"ValidationResult(valid=False, errors={len(self.errors)})"


class Manifest:
    """High-level interface for SCP manifests.

    Provides convenient methods for loading, manipulating, and validating
    scp.yaml files.

    Example:
        >>> manifest = Manifest.from_file("scp.yaml")
        >>> print(manifest.urn)
        urn:scp:payment-service
        >>> dep = manifest.get_dependency("urn:scp:user-service")
        >>> print(dep.criticality)
        required
    """

    def __init__(self, data: SCPManifest):
        """Initialize with parsed manifest data.

        Args:
            data: Parsed SCPManifest model
        """
        self._data = data

    @classmethod
    def from_file(cls, path: Path | str) -> Self:
        """Load manifest from a file.

        Args:
            path: Path to scp.yaml file

        Returns:
            Manifest instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If manifest is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest file not found: {path}")

        with open(path, "r") as f:
            yaml_data = yaml.safe_load(f)

        return cls.from_dict(yaml_data)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> Self:
        """Load manifest from YAML string.

        Args:
            yaml_str: YAML content as string

        Returns:
            Manifest instance

        Raises:
            ValidationError: If manifest is invalid
        """
        yaml_data = yaml.safe_load(yaml_str)
        return cls.from_dict(yaml_data)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Load manifest from dictionary.

        Args:
            data: Parsed YAML data

        Returns:
            Manifest instance

        Raises:
            ValidationError: If manifest is invalid
        """
        manifest = SCPManifest.model_validate(data)
        return cls(manifest)

    def to_yaml(self) -> str:
        """Export manifest to YAML string.

        Returns:
            YAML representation
        """
        data = self._data.model_dump(mode="json", exclude_none=True)
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def to_dict(self) -> dict:
        """Export manifest to dictionary.

        Returns:
            Dictionary representation
        """
        return self._data.model_dump(mode="json", exclude_none=True)

    def validate(self) -> ValidationResult:
        """Validate the manifest.

        Returns:
            ValidationResult with any errors
        """
        try:
            # Re-validate the model
            SCPManifest.model_validate(self._data.model_dump())
            return ValidationResult(valid=True)
        except ValidationError as e:
            errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
            return ValidationResult(valid=False, errors=errors)

    def get_dependency(self, urn: str) -> Dependency | None:
        """Get a dependency by system URN.

        Args:
            urn: System URN to search for

        Returns:
            Dependency if found, None otherwise
        """
        if not self._data.depends:
            return None

        for dep in self._data.depends:
            if dep.system == urn:
                return dep
        return None

    def get_capability(self, name: str) -> Capability | None:
        """Get a capability by name.

        Args:
            name: Capability name to search for

        Returns:
            Capability if found, None otherwise
        """
        if not self._data.provides:
            return None

        for cap in self._data.provides:
            if cap.capability == name:
                return cap
        return None

    # Convenience properties
    @property
    def urn(self) -> str:
        """Get system URN."""
        return self._data.system.urn

    @property
    def name(self) -> str:
        """Get system name."""
        return self._data.system.name

    @property
    def tier(self) -> int | None:
        """Get system tier (criticality)."""
        if self._data.system.classification:
            return self._data.system.classification.tier
        return None

    @property
    def domain(self) -> str | None:
        """Get system domain."""
        if self._data.system.classification:
            return self._data.system.classification.domain
        return None

    @property
    def team(self) -> str | None:
        """Get owning team."""
        if self._data.ownership:
            return self._data.ownership.team
        return None

    @property
    def dependencies(self) -> list[Dependency]:
        """Get all dependencies."""
        return self._data.depends or []

    @property
    def capabilities(self) -> list[Capability]:
        """Get all capabilities."""
        return self._data.provides or []

    @property
    def otel_service_name(self) -> str | None:
        """Get production OpenTelemetry service name."""
        return self._data.otel_service_name

    @property
    def data(self) -> SCPManifest:
        """Get underlying Pydantic model."""
        return self._data

    def __repr__(self) -> str:
        return f"Manifest(urn='{self.urn}', name='{self.name}')"
