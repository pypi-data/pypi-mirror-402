"""SCP SDK - Python SDK for System Capability Protocol.

Provides programmatic access to SCP manifests and graphs, plus a framework
for building integrations and runtime instrumentation.
"""

__version__ = "0.1.0"

# Core models
from .core.models import (
    SCPManifest,
    System,
    Ownership,
    Capability,
    Dependency,
    Classification,
    Contact,
    Contract,
    SLA,
    Constraints,
    Runtime,
    Environment,
    FailureMode,
    SecurityExtension,
    ValidationIssue,
)

# High-level APIs
from .core.manifest import Manifest
from .core.graph import Graph, SystemNode, DependencyEdge
from .core.export import export_graph_json, import_graph_json

# Integration framework
from .integrations.base import (
    IntegrationConfig,
    IntegrationValidator,
    IntegrationResult,
)

# Utilities
from .utils import TierUtils

# Testing utilities
from .testing import (
    GraphFixture,
    ManifestFixture,
    CLITestHelper,
    MockConfig,
    create_mock_client,
)

__all__ = [
    "__version__",
    # Models
    "SCPManifest",
    "System",
    "Ownership",
    "Capability",
    "Dependency",
    "Classification",
    "Contact",
    "Contract",
    "SLA",
    "Constraints",
    "Runtime",
    "Environment",
    "FailureMode",
    "SecurityExtension",
    "ValidationIssue",
    # High-level APIs
    "Manifest",
    "Graph",
    "SystemNode",
    "DependencyEdge",
    # Export/Import
    "export_graph_json",
    "import_graph_json",
    # Integration framework
    "IntegrationConfig",
    "IntegrationValidator",
    "IntegrationResult",
    # Utilities
    "TierUtils",
    # Testing
    "GraphFixture",
    "ManifestFixture",
    "CLITestHelper",
    "MockConfig",
    "create_mock_client",
]
