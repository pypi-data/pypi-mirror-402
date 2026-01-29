"""Pydantic models for SCP (System Capability Protocol) manifests.

These models match the SCP v0.1.0 schema specification.
"""

from typing import Literal
from pydantic import BaseModel, Field


# ============================================================================
# Nested Types
# ============================================================================


class Contact(BaseModel):
    """Contact channel for a team.

    Defines how to reach a team through various communication channels.
    Used in ownership section for incident response and escalation.
    """

    type: Literal["oncall", "slack", "email", "teams", "pagerduty", "opsgenie"] = Field(
        description="Type of contact channel (oncall, slack, email, teams, pagerduty, opsgenie)"
    )
    ref: str = Field(
        description="Reference identifier for the contact (e.g., Slack channel ID, email address, PagerDuty service ID)"
    )


class Contract(BaseModel):
    """API contract specification reference.

    Points to machine-readable API specifications for capabilities.
    Enables automated validation, code generation, and contract testing.
    """

    type: (
        Literal["openapi", "asyncapi", "protobuf", "graphql", "avro", "jsonschema"]
        | None
    ) = Field(default=None, description="Type of contract specification format")
    ref: str | None = Field(
        default=None,
        description="URI or path to the contract file (e.g., './openapi.yaml', 'https://api.example.com/spec')",
    )


class SLA(BaseModel):
    """Service level agreement targets.

    Defines performance and reliability commitments for a capability.
    Used for monitoring, alerting, and capacity planning.
    """

    availability: str | None = Field(
        default=None,
        description="Target availability percentage (e.g., '99.95%', '99.9%')",
    )
    latency_p50_ms: int | None = Field(
        default=None,
        description="Median (50th percentile) latency target in milliseconds",
    )
    latency_p99_ms: int | None = Field(
        default=None, description="99th percentile latency target in milliseconds"
    )
    throughput_rps: int | None = Field(
        default=None, description="Target throughput in requests per second"
    )


class RetryConfig(BaseModel):
    """Retry configuration for dependencies.

    Defines how a system should retry failed requests to a dependency.
    Part of resilience engineering best practices.
    """

    max_attempts: int | None = Field(
        default=None, description="Maximum number of retry attempts before giving up"
    )
    backoff: Literal["none", "linear", "exponential"] | None = Field(
        default=None,
        description="Backoff strategy between retries (none, linear, exponential)",
    )


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration.

    Implements the circuit breaker pattern to prevent cascading failures.
    When failure threshold is met, the circuit opens and fails fast.
    """

    failure_threshold: int | None = Field(
        default=None,
        description="Number of consecutive failures before opening the circuit",
    )
    reset_timeout_ms: int | None = Field(
        default=None,
        description="Time in milliseconds to wait before attempting to close the circuit",
    )


class SecurityConstraints(BaseModel):
    """Security-related constraints.

    Defines security requirements and configurations for the system.
    Used for compliance validation and security posture assessment.
    """

    authentication: list[str] | None = Field(
        default=None,
        description="Required authentication methods (e.g., ['oauth2', 'mTLS', 'api-key'])",
    )
    data_classification: str | None = Field(
        default=None,
        description="Data classification level (e.g., 'public', 'internal', 'confidential', 'restricted')",
    )
    encryption: dict[str, bool] | None = Field(
        default=None,
        description="Encryption requirements with keys 'at_rest' and 'in_transit'",
    )


class ComplianceConstraints(BaseModel):
    """Compliance-related constraints.

    Defines regulatory and compliance requirements.
    Used for audit trails and compliance reporting.
    """

    frameworks: list[str] | None = Field(
        default=None,
        description="Applicable compliance frameworks (e.g., ['SOC2', 'HIPAA', 'GDPR', 'PCI-DSS'])",
    )
    data_residency: list[str] | None = Field(
        default=None,
        description="Required data residency regions (e.g., ['US', 'EU', 'APAC'])",
    )
    retention_days: int | None = Field(
        default=None, description="Data retention period in days"
    )


class OperationalConstraints(BaseModel):
    """Operational constraints.

    Defines operational requirements and limitations.
    Used for capacity planning and deployment automation.
    """

    max_replicas: int | None = Field(
        default=None, description="Maximum number of instances/pods allowed"
    )
    min_replicas: int | None = Field(
        default=None, description="Minimum number of instances/pods required"
    )
    deployment_windows: list[str] | None = Field(
        default=None,
        description="Allowed deployment time windows (e.g., ['mon-fri 02:00-04:00 UTC'])",
    )


class KubernetesRuntime(BaseModel):
    """Kubernetes deployment information.

    Identifies Kubernetes resources for the system.
    Used for runtime discovery and monitoring integration.
    """

    namespace: str | None = Field(
        default=None, description="Kubernetes namespace where the system is deployed"
    )
    deployment: str | None = Field(
        default=None, description="Name of the Kubernetes Deployment resource"
    )
    service: str | None = Field(
        default=None, description="Name of the Kubernetes Service resource"
    )


class AWSRuntime(BaseModel):
    """AWS deployment information.

    Identifies AWS resources for the system.
    Used for cloud resource discovery and cost allocation.
    """

    account_id: str | None = Field(default=None, description="AWS Account ID")
    region: str | None = Field(
        default=None, description="AWS Region (e.g., 'us-west-2')"
    )
    arn: str | None = Field(default=None, description="Resource ARN")


class Environment(BaseModel):
    """Runtime environment configuration."""

    otel_service_name: str | None = Field(
        default=None, description="OpenTelemetry service name for this environment"
    )
    endpoints: list[str] | None = Field(
        default=None, description="Public or internal endpoints (URLs)"
    )
    kubernetes: KubernetesRuntime | None = Field(
        default=None, description="Kubernetes deployment details"
    )
    aws: AWSRuntime | None = Field(default=None, description="AWS deployment details")


class FailureModeThresholds(BaseModel):
    """Thresholds for failure mode detection."""

    warning_ms: int | None = None
    critical_ms: int | None = None


class SecurityExtension(BaseModel):
    """OpenC2-inspired security capability metadata.

    Used to describe what actions a security tool supports,
    enabling SOAR autodiscovery of security controls.
    """

    actuator_profile: str | None = Field(
        default=None,
        description="Security actuator profile (e.g., 'edr', 'siem', 'slpf')",
    )
    actions: list[str] = Field(
        default=[], description="Supported actions (e.g., 'query', 'contain', 'deny')"
    )
    targets: list[str] = Field(
        default=[], description="Supported targets (e.g., 'device', 'ipv4_net', 'file')"
    )


# ============================================================================
# Top-Level Types
# ============================================================================


class Classification(BaseModel):
    """System classification metadata.

    Categorizes systems by criticality,domain, and other attributes.
    Used for prioritization, resource allocation, and impact analysis.
    """

    tier: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="Criticality tier (1-5), where 1 is most critical",
    )
    domain: str | None = Field(
        default=None,
        description="Domain or bounded context (e.g., 'payments', 'identity')",
    )
    tags: list[str] | None = Field(
        default=None, description="Arbitrary labels for filtering and categorization"
    )


class System(BaseModel):
    """Core system identification."""

    urn: str = Field(
        ...,
        pattern=r"^urn:scp:[a-z0-9-]+(:[a-z0-9-]+)?$",
        description="Unique resource name following pattern 'urn:scp:service-name' or 'urn:scp:namespace:service-name'",
    )
    name: str = Field(description="Human-readable system name")
    description: str | None = Field(
        default=None,
        description="Brief description of the system's purpose and functionality",
    )
    version: str | None = Field(
        default=None, description="System version (e.g., '1.0.0', '2.3.1-beta')"
    )
    classification: Classification | None = Field(
        default=None,
        description="Classification metadata including tier, domain, and tags",
    )


class Ownership(BaseModel):
    """Team ownership and contact information.

    Defines who is responsible for the system and how to reach them.
    Critical for incident response and operational excellence.
    """

    team: str = Field(description="Team name or identifier responsible for the system")
    contacts: list[Contact] | None = Field(
        default=None,
        description="Contact channels for reaching the team (Slack, PagerDuty, email, etc.)",
    )
    escalation: list[str] | None = Field(
        default=None, description="Escalation chain, ordered list of contacts or teams"
    )


class Capability(BaseModel):
    """A capability provided by the system.

    Represents a service, API, event stream, or data store that the system provides.
    Each capability can have contracts, SLAs, and security metadata.

    Example:
        >>> capability = Capability(
        ...     capability="process-payment",
        ...     type="rest",
        ...     contract=Contract(type="openapi", ref="./openapi.yaml"),
        ...     sla=SLA(availability="99.95%", latency_p99_ms=500)
        ... )
    """

    model_config = {"populate_by_name": True}

    capability: str = Field(
        description="Unique capability identifier (e.g., 'user-authentication', 'payment-processing')"
    )
    type: Literal["rest", "grpc", "graphql", "event", "data", "stream"] = Field(
        description="Type of capability: rest (HTTP API), grpc, graphql, event (pub/sub), data (database), or stream"
    )
    contract: Contract | None = Field(
        default=None, description="Machine-readable API contract specification"
    )
    sla: SLA | None = Field(
        default=None, description="Service level agreement targets for this capability"
    )
    topics: list[str] | None = Field(
        default=None,
        description="Event topics or data streams (relevant for 'event' and 'stream' types)",
    )
    x_security: SecurityExtension | None = Field(
        default=None,
        alias="x-security",
        description="Security capability metadata for SOAR autodiscovery (OpenC2-inspired)",
    )


class Dependency(BaseModel):
    """A dependency on another system.

    Defines a relationship where this system relies on another system's capability.
    Includes resilience patterns (retry, circuit breaker) and criticality.

    Example:
        >>> dep = Dependency(
        ...     system="urn:scp:auth-service",
        ...     capability="verify-token",
        ...     type="rest",
        ...     criticality="required",
        ...     timeout_ms=500,
        ...     retry=RetryConfig(max_attempts=3, backoff="exponential")
        ... )
    """

    system: str = Field(
        ...,
        pattern=r"^urn:scp:[a-z0-9-]+(:[a-z0-9-]+)?$",
        description="URN of the system being depended on",
    )
    capability: str | None = Field(
        default=None,
        description="Specific capability being consumed (optional but recommended)",
    )
    type: Literal["rest", "grpc", "graphql", "event", "data", "stream"] = Field(
        description="Type of interaction (must match the provided capability type)"
    )
    criticality: Literal["required", "degraded", "optional"] = Field(
        description="Impact if this dependency fails (required=outage, degraded=reduced functionality, optional=no impact)"
    )
    failure_mode: (
        Literal["fail-fast", "circuit-break", "fallback", "queue-buffer", "retry"]
        | None
    ) = Field(default=None, description="Expected behavior when dependency fails")
    timeout_ms: int | None = Field(
        default=None, description="Client-side timeout in milliseconds"
    )
    retry: RetryConfig | None = Field(
        default=None, description="Retry policy configuration"
    )
    circuit_breaker: CircuitBreakerConfig | None = Field(
        default=None, description="Circuit breaker configuration"
    )
    topics: list[str] | None = Field(
        default=None,
        description="Specific topics or streams consumed (for event/stream types)",
    )
    access: Literal["read", "write", "read-write"] | None = Field(
        default=None,
        description="Data access level (mainly for data/database dependencies)",
    )


class Constraints(BaseModel):
    """System constraints.

    Groups all constraint-related configurations covering security, compliance,
    and operational requirements.
    """

    security: SecurityConstraints | None = Field(
        default=None, description="Security constraints and requirements"
    )
    compliance: ComplianceConstraints | None = Field(
        default=None, description="Compliance and regulatory requirements"
    )
    operational: OperationalConstraints | None = Field(
        default=None, description="Operational limits and requirements"
    )


class Runtime(BaseModel):
    """Runtime environment configurations.

    Maps deployment environments (e.g., 'production', 'staging') to their
    specific configurations.
    """

    environments: dict[str, Environment] | None = Field(
        default=None,
        description="Dictionary mapping environment names to their configurations",
    )


class FailureMode(BaseModel):
    """Known failure mode and its characteristics.

    Documents specific ways the system might fail and the expected impact.
    Essential for failure mode and effects analysis (FMEA) and game days.
    """

    mode: str = Field(
        description="Name or title of the failure mode (e.g., 'database-latency-spike', 'cache-miss-storm')"
    )
    impact: Literal[
        "total-outage",
        "partial-outage",
        "degraded-experience",
        "data-inconsistency",
        "silent-failure",
    ] = Field(description="Severity of the impact on the system's users")
    detection: str | None = Field(
        default=None, description="How this failure is detected (alerts, metrics, logs)"
    )
    recovery: str | None = Field(
        default=None, description="Automated or manual recovery steps"
    )
    degraded_behavior: str | None = Field(
        default=None,
        description="Description of how the system behaves while in this failure mode",
    )
    mttr_target_minutes: int | None = Field(
        default=None, description="Target Mean Time To Recovery in minutes"
    )
    thresholds: FailureModeThresholds | None = Field(
        default=None, description="Metric thresholds defining this failure mode"
    )


# ============================================================================
# Root Model
# ============================================================================


class SCPManifest(BaseModel):
    """Root SCP manifest model.

    This represents a complete scp.yaml file.
    It aggregates all information about a system into a single document.
    """

    scp: str = Field(description="SCP schema version (e.g., '0.1.0')")
    system: System = Field(description="Core system identification")
    ownership: Ownership | None = Field(
        default=None, description="Team ownership and contacts"
    )
    provides: list[Capability] | None = Field(
        default=None, description="List of capabilities provided by this system"
    )
    depends: list[Dependency] | None = Field(
        default=None, description="List of dependencies on other systems"
    )
    constraints: Constraints | None = Field(
        default=None,
        description="System constraints (security, compliance, operational)",
    )
    runtime: Runtime | None = Field(
        default=None, description="Runtime environment configurations"
    )
    failure_modes: list[FailureMode] | None = Field(
        default=None, description="Known failure modes and analysis"
    )

    @property
    def urn(self) -> str:
        """Convenience accessor for system URN."""
        return self.system.urn

    @property
    def otel_service_name(self) -> str | None:
        """Get the production OTel service name if defined."""
        if self.runtime and self.runtime.environments:
            prod = self.runtime.environments.get("production")
            if prod:
                return prod.otel_service_name
        return None


# ============================================================================
# Validation Types
# ============================================================================


class ValidationIssue(BaseModel):
    """Graph validation issue.

    Used by Graph.validate() to report structural or semantic problems.
    Can represent errors (broken graph), warnings, or informational notices.
    """

    severity: Literal["error", "warning", "info"] = Field(
        description="Severity level of the issue"
    )
    code: str = Field(
        description="Unique error code (e.g., 'MISSING_DEPENDENCY_TARGET')"
    )
    message: str = Field(description="Human-readable description of the issue")
    context: dict[str, str] = Field(
        default={},
        description="Additional context for debugging (e.g., affected URNs, edge details)",
    )
