"""Base classes for building SCP integrations.

Provides reusable patterns for configuration loading, validation, and result reporting.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel, Field

from ..core.graph import Graph, SystemNode
from ..core.models import ValidationIssue


class IntegrationConfig(BaseModel):
    """Base class for integration configurations.

    Provides standardized YAML loading with auto-discovery of config files.

    Example:
        >>> class MyConfig(IntegrationConfig):
        >>>     api_key: str
        >>>     endpoint: str
        >>>
        >>> config = MyConfig.load()  # Auto-discovers config.yaml
    """

    @classmethod
    def load(cls, path: Path | None = None) -> Self:
        """Load configuration from YAML file.

        Auto-discovery search order:
        1. Provided path
        2. ./config.yaml (current directory)
        3. Returns default instance if no config found

        Args:
            path: Optional path to config file

        Returns:
            Configuration instance

        Raises:
            FileNotFoundError: If explicit path provided but doesn't exist
            ValueError: If YAML is invalid
        """
        # If explicit path provided, it must exist
        if path is not None:
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)

        # Auto-discovery: check current directory
        cwd_config = Path.cwd() / "config.yaml"
        if cwd_config.exists():
            with open(cwd_config) as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)

        # No config found, return defaults
        return cls()

    def to_yaml(self) -> str:
        """Export configuration to YAML string.

        Returns:
            YAML representation of config
        """
        return yaml.dump(
            self.model_dump(exclude_none=True),
            default_flow_style=False,
            sort_keys=False,
        )


class IntegrationResult(BaseModel):
    """Standard result reporting for integration operations.

    Provides consistent structure for reporting success/failure, counts,
    and detailed error/warning information.

    Example:
        >>> result = IntegrationResult()
        >>> result.items_processed = 10
        >>> result.items_failed = 2
        >>> result.errors.append({"system": "foo", "error": "bar"})
        >>> result.success = result.items_failed == 0
    """

    success: bool = True
    items_processed: int = 0
    items_failed: int = 0
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)

    def add_error(self, **kwargs: Any) -> None:
        """Add an error to the result.

        Args:
            **kwargs: Error details (e.g., system="foo", message="bar")
        """
        self.errors.append(kwargs)
        self.items_failed += 1
        self.success = False

    def add_warning(self, **kwargs: Any) -> None:
        """Add a warning to the result.

        Args:
            **kwargs: Warning details
        """
        self.warnings.append(kwargs)


class IntegrationValidator(ABC):
    """Abstract base class for integration-specific validation.

    Subclass this to implement custom validation logic for your integration.

    Example:
        >>> class MyValidator(IntegrationValidator):
        >>>     def validate_system(self, system):
        >>>         issues = []
        >>>         if not system.name:
        >>>             issues.append(ValidationIssue(
        >>>                 severity="error",
        >>>                 code="MISSING_NAME",
        >>>                 message="System missing name"
        >>>             ))
        >>>         return issues
        >>>
        >>>     def validate_graph(self, graph):
        >>>         return graph.validate()  # Use SDK validation
    """

    @abstractmethod
    def validate_system(self, system: SystemNode) -> list[ValidationIssue]:
        """Validate a single system node.

        Args:
            system: System node to validate

        Returns:
            List of validation issues (empty if valid)
        """
        pass

    @abstractmethod
    def validate_graph(self, graph: Graph) -> list[ValidationIssue]:
        """Validate entire graph.

        Args:
            graph: Graph to validate

        Returns:
            List of validation issues (empty if valid)
        """
        pass
