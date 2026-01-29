"""Tests for export/import functionality."""

from scp_sdk import (
    SCPManifest,
    System,
    Ownership,
    Contact,
    Capability,
    Dependency,
    Classification,
    export_graph_json,
    import_graph_json,
)
from scp_sdk.core.models import (
    Contract,
    SLA,
    RetryConfig,
    CircuitBreakerConfig,
    Constraints,
    SecurityConstraints,
    ComplianceConstraints,
    OperationalConstraints,
    Runtime,
    Environment,
    KubernetesRuntime,
    AWSRuntime,
    FailureMode,
    FailureModeThresholds,
    SecurityExtension,
)


def test_export_simple_manifest():
    """Test exporting a simple manifest to JSON."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
    )

    result = export_graph_json([manifest])

    assert "nodes" in result
    assert "edges" in result
    assert "meta" in result
    assert result["meta"]["systems_count"] == 1
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["id"] == "urn:scp:test:service-a"
    assert result["nodes"][0]["name"] == "Service A"


def test_export_with_classification():
    """Test exporting manifest with classification."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(
            urn="urn:scp:test:service-a",
            name="Service A",
            classification=Classification(tier=1, domain="payments"),
        ),
    )

    result = export_graph_json([manifest])

    node = result["nodes"][0]
    assert node["tier"] == 1
    assert node["domain"] == "payments"


def test_export_with_ownership():
    """Test exporting manifest with ownership."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
        ownership=Ownership(
            team="platform",
            contacts=[Contact(type="email", ref="team@example.com")],
            escalation=["lead", "manager"],
        ),
    )

    result = export_graph_json([manifest])

    node = result["nodes"][0]
    assert node["team"] == "platform"
    assert len(node["contacts"]) == 1
    assert node["contacts"][0]["type"] == "email"
    assert node["escalation"] == ["lead", "manager"]


def test_export_with_dependencies():
    """Test exporting manifest with dependencies."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
        depends=[
            Dependency(
                system="urn:scp:test:service-b",
                capability="api",
                type="rest",
                criticality="required",
                failure_mode="circuit-break",
            )
        ],
    )

    result = export_graph_json([manifest])

    # Should have 2 nodes (service-a + stub for service-b)
    assert len(result["nodes"]) == 2
    systems = [n for n in result["nodes"] if n["type"] == "System"]
    assert len(systems) == 2

    # Check stub node
    stub = next(n for n in systems if n.get("stub"))
    assert stub["id"] == "urn:scp:test:service-b"

    # Check dependency edge
    assert len(result["edges"]) == 1
    edge = result["edges"][0]
    assert edge["from"] == "urn:scp:test:service-a"
    assert edge["to"] == "urn:scp:test:service-b"
    assert edge["type"] == "DEPENDS_ON"
    assert edge["capability"] == "api"


def test_export_with_capabilities():
    """Test exporting manifest with capabilities."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
        provides=[Capability(capability="user-api", type="rest")],
    )

    result = export_graph_json([manifest])

    # Should have 2 nodes (system + capability)
    assert len(result["nodes"]) == 2
    cap = next(n for n in result["nodes"] if n["type"] == "Capability")
    assert cap["name"] == "user-api"
    assert cap["capability_type"] == "rest"

    # Check PROVIDES edge
    provides_edges = [e for e in result["edges"] if e["type"] == "PROVIDES"]
    assert len(provides_edges) == 1


def test_roundtrip_with_security_extension():
    """Test that x-security extension survives export/import roundtrip."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:security-tool", name="Security Tool"),
        provides=[
            Capability(
                capability="threat-detection",
                type="rest",
                **{
                    "x-security": SecurityExtension(
                        actuator_profile="edr",
                        actions=["query", "contain"],
                        targets=["device", "process"],
                    )
                },
            )
        ],
    )

    # Export then import
    exported = export_graph_json([manifest])
    imported = import_graph_json(exported)

    # Verify x-security was preserved
    assert len(imported) == 1
    assert imported[0].provides is not None
    assert len(imported[0].provides) == 1
    cap = imported[0].provides[0]
    assert cap.x_security is not None
    assert cap.x_security.actuator_profile == "edr"
    assert cap.x_security.actions == ["query", "contain"]
    assert cap.x_security.targets == ["device", "process"]


def test_export_replaces_stubs():
    """Test that real nodes replace stub nodes."""
    manifest_a = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
        depends=[
            Dependency(
                system="urn:scp:test:service-b", type="rest", criticality="required"
            )
        ],
    )

    manifest_b = SCPManifest(
        scp="0.1.0",
        system=System(
            urn="urn:scp:test:service-b",
            name="Service B Real Name",
            classification=Classification(tier=2),
        ),
    )

    result = export_graph_json([manifest_a, manifest_b])

    # Service B should be real, not stub
    service_b = next(n for n in result["nodes"] if n["id"] == "urn:scp:test:service-b")
    assert not service_b.get("stub")
    assert service_b["name"] == "Service B Real Name"
    assert service_b["tier"] == 2


def test_import_simple_graph():
    """Test importing a simple graph."""
    data = {
        "nodes": [
            {
                "id": "urn:scp:test:service-a",
                "type": "System",
                "name": "Service A",
                "tier": None,
                "domain": None,
                "team": None,
                "contacts": [],
                "escalation": [],
            }
        ],
        "edges": [],
    }

    manifests = import_graph_json(data)

    assert len(manifests) == 1
    assert manifests[0].system.urn == "urn:scp:test:service-a"
    assert manifests[0].system.name == "Service A"


def test_import_with_classification():
    """Test importing graph with classification."""
    data = {
        "nodes": [
            {
                "id": "urn:scp:test:service-a",
                "type": "System",
                "name": "Service A",
                "tier": 1,
                "domain": "payments",
            }
        ],
        "edges": [],
    }

    manifests = import_graph_json(data)

    assert manifests[0].system.classification is not None
    assert manifests[0].system.classification.tier == 1
    assert manifests[0].system.classification.domain == "payments"


def test_import_with_ownership():
    """Test importing graph with ownership."""
    data = {
        "nodes": [
            {
                "id": "urn:scp:test:service-a",
                "type": "System",
                "name": "Service A",
                "team": "platform",
                "contacts": [{"type": "email", "ref": "team@example.com"}],
                "escalation": ["lead"],
            }
        ],
        "edges": [],
    }

    manifests = import_graph_json(data)

    assert manifests[0].ownership is not None
    assert manifests[0].ownership.team == "platform"
    assert len(manifests[0].ownership.contacts) == 1
    assert manifests[0].ownership.contacts[0].type == "email"


def test_import_skips_stubs():
    """Test that stub nodes are not imported."""
    data = {
        "nodes": [
            {
                "id": "urn:scp:test:service-a",
                "type": "System",
                "name": "Service A",
                "stub": False,
            },
            {
                "id": "urn:scp:test:external",
                "type": "System",
                "name": "External",
                "stub": True,  # Stub, should be skipped
            },
        ],
        "edges": [],
    }

    manifests = import_graph_json(data)

    # Only service-a should be imported
    assert len(manifests) == 1
    assert manifests[0].system.urn == "urn:scp:test:service-a"


def test_roundtrip_preservation():
    """Test that export->import preserves data."""
    original = SCPManifest(
        scp="0.1.0",
        system=System(
            urn="urn:scp:test:service-a",
            name="Service A",
            classification=Classification(tier=2, domain="payments"),
        ),
        ownership=Ownership(
            team="platform-team",
            contacts=[Contact(type="email", ref="team@example.com")],
        ),
    )

    # Export then import
    exported = export_graph_json([original])
    imported = import_graph_json(exported)

    # Verify preservation
    assert len(imported) == 1
    manifest = imported[0]
    assert manifest.system.urn == original.system.urn
    assert manifest.system.name == original.system.name
    assert manifest.system.classification.tier == original.system.classification.tier
    assert manifest.ownership.team == original.ownership.team


# =============================================================================
# New tests for complete field coverage
# =============================================================================


def test_export_with_system_description_and_version():
    """Test exporting manifest with system description, version and tags."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(
            urn="urn:scp:test:service-a",
            name="Service A",
            description="A test service for payments",
            version="2.3.1",
            classification=Classification(
                tier=1, domain="payments", tags=["critical", "pci"]
            ),
        ),
    )

    result = export_graph_json([manifest])
    node = result["nodes"][0]

    assert node["description"] == "A test service for payments"
    assert node["version"] == "2.3.1"
    assert node["scp_version"] == "0.1.0"
    assert node["tags"] == ["critical", "pci"]


def test_export_with_capability_contract_and_sla():
    """Test exporting manifest with capability contract and SLA."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
        provides=[
            Capability(
                capability="payment-api",
                type="rest",
                contract=Contract(type="openapi", ref="./openapi.yaml"),
                sla=SLA(
                    availability="99.95%",
                    latency_p50_ms=50,
                    latency_p99_ms=200,
                    throughput_rps=1000,
                ),
                topics=["payments.completed", "payments.failed"],
            )
        ],
    )

    result = export_graph_json([manifest])
    cap = next(n for n in result["nodes"] if n["type"] == "Capability")

    assert cap["contract"] == {"type": "openapi", "ref": "./openapi.yaml"}
    assert cap["sla"]["availability"] == "99.95%"
    assert cap["sla"]["latency_p50_ms"] == 50
    assert cap["sla"]["latency_p99_ms"] == 200
    assert cap["sla"]["throughput_rps"] == 1000
    assert cap["topics"] == ["payments.completed", "payments.failed"]


def test_export_with_dependency_resilience_config():
    """Test exporting manifest with full dependency resilience configuration."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
        depends=[
            Dependency(
                system="urn:scp:test:database",
                capability="user-data",
                type="data",
                criticality="required",
                failure_mode="circuit-break",
                timeout_ms=5000,
                retry=RetryConfig(max_attempts=3, backoff="exponential"),
                circuit_breaker=CircuitBreakerConfig(
                    failure_threshold=5, reset_timeout_ms=30000
                ),
                topics=["users.updates"],
                access="read-write",
            )
        ],
    )

    result = export_graph_json([manifest])
    edge = result["edges"][0]

    assert edge["dependency_type"] == "data"
    assert edge["timeout_ms"] == 5000
    assert edge["retry"] == {"max_attempts": 3, "backoff": "exponential"}
    assert edge["circuit_breaker"] == {
        "failure_threshold": 5,
        "reset_timeout_ms": 30000,
    }
    assert edge["topics"] == ["users.updates"]
    assert edge["access"] == "read-write"


def test_export_with_constraints():
    """Test exporting manifest with full constraints section."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
        constraints=Constraints(
            security=SecurityConstraints(
                authentication=["oauth2", "mTLS"],
                data_classification="confidential",
                encryption={"at_rest": True, "in_transit": True},
            ),
            compliance=ComplianceConstraints(
                frameworks=["SOC2", "HIPAA"],
                data_residency=["US", "EU"],
                retention_days=365,
            ),
            operational=OperationalConstraints(
                max_replicas=10,
                min_replicas=2,
                deployment_windows=["mon-fri 02:00-04:00 UTC"],
            ),
        ),
    )

    result = export_graph_json([manifest])
    node = result["nodes"][0]

    assert node["constraints"]["security"]["authentication"] == ["oauth2", "mTLS"]
    assert node["constraints"]["security"]["data_classification"] == "confidential"
    assert node["constraints"]["security"]["encryption"] == {
        "at_rest": True,
        "in_transit": True,
    }
    assert node["constraints"]["compliance"]["frameworks"] == ["SOC2", "HIPAA"]
    assert node["constraints"]["compliance"]["data_residency"] == ["US", "EU"]
    assert node["constraints"]["compliance"]["retention_days"] == 365
    assert node["constraints"]["operational"]["max_replicas"] == 10
    assert node["constraints"]["operational"]["min_replicas"] == 2


def test_export_with_runtime():
    """Test exporting manifest with runtime environments."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
        runtime=Runtime(
            environments={
                "production": Environment(
                    otel_service_name="service-a-prod",
                    endpoints=["https://api.example.com"],
                    kubernetes=KubernetesRuntime(
                        namespace="production",
                        deployment="service-a",
                        service="service-a-svc",
                    ),
                    aws=AWSRuntime(
                        account_id="123456789012",
                        region="us-west-2",
                        arn="arn:aws:ecs:us-west-2:123456789012:service/service-a",
                    ),
                ),
                "staging": Environment(
                    otel_service_name="service-a-staging",
                    endpoints=["https://staging.example.com"],
                ),
            }
        ),
    )

    result = export_graph_json([manifest])
    node = result["nodes"][0]

    prod = node["runtime"]["environments"]["production"]
    assert prod["otel_service_name"] == "service-a-prod"
    assert prod["endpoints"] == ["https://api.example.com"]
    assert prod["kubernetes"]["namespace"] == "production"
    assert prod["kubernetes"]["deployment"] == "service-a"
    assert prod["aws"]["account_id"] == "123456789012"
    assert prod["aws"]["region"] == "us-west-2"

    staging = node["runtime"]["environments"]["staging"]
    assert staging["otel_service_name"] == "service-a-staging"


def test_export_with_failure_modes():
    """Test exporting manifest with failure modes."""
    manifest = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:service-a", name="Service A"),
        failure_modes=[
            FailureMode(
                mode="database-latency-spike",
                impact="degraded-experience",
                detection="P99 latency > 500ms for 5 minutes",
                recovery="Scale up database read replicas",
                degraded_behavior="Slower response times, cached data served",
                mttr_target_minutes=15,
                thresholds=FailureModeThresholds(warning_ms=200, critical_ms=500),
            ),
            FailureMode(
                mode="cache-miss-storm",
                impact="partial-outage",
                detection="Cache hit ratio < 50%",
                recovery="Warm cache, increase TTL",
            ),
        ],
    )

    result = export_graph_json([manifest])
    node = result["nodes"][0]

    assert len(node["failure_modes"]) == 2

    fm1 = node["failure_modes"][0]
    assert fm1["mode"] == "database-latency-spike"
    assert fm1["impact"] == "degraded-experience"
    assert fm1["detection"] == "P99 latency > 500ms for 5 minutes"
    assert fm1["recovery"] == "Scale up database read replicas"
    assert fm1["degraded_behavior"] == "Slower response times, cached data served"
    assert fm1["mttr_target_minutes"] == 15
    assert fm1["thresholds"]["warning_ms"] == 200
    assert fm1["thresholds"]["critical_ms"] == 500

    fm2 = node["failure_modes"][1]
    assert fm2["mode"] == "cache-miss-storm"
    assert fm2["impact"] == "partial-outage"


def test_complete_roundtrip_preservation():
    """Test that a fully-populated manifest survives export->import roundtrip."""
    original = SCPManifest(
        scp="0.2.0",
        system=System(
            urn="urn:scp:test:complete-service",
            name="Complete Service",
            description="A fully-featured service for testing",
            version="3.0.0",
            classification=Classification(
                tier=1, domain="core", tags=["mission-critical"]
            ),
        ),
        ownership=Ownership(
            team="platform-team",
            contacts=[
                Contact(type="slack", ref="#platform-oncall"),
                Contact(type="pagerduty", ref="PABCD12"),
            ],
            escalation=["tech-lead", "engineering-manager", "vp-engineering"],
        ),
        provides=[
            Capability(
                capability="main-api",
                type="rest",
                contract=Contract(type="openapi", ref="./api.yaml"),
                sla=SLA(availability="99.99%", latency_p99_ms=100),
                topics=["events.published"],
            ),
        ],
        depends=[
            Dependency(
                system="urn:scp:test:auth-service",
                capability="verify-token",
                type="grpc",
                criticality="required",
                failure_mode="fail-fast",
                timeout_ms=100,
                retry=RetryConfig(max_attempts=2, backoff="exponential"),
            ),
        ],
        constraints=Constraints(
            security=SecurityConstraints(
                authentication=["mTLS"],
                data_classification="restricted",
            ),
            compliance=ComplianceConstraints(
                frameworks=["PCI-DSS"],
                retention_days=2555,
            ),
            operational=OperationalConstraints(
                min_replicas=3,
                max_replicas=20,
            ),
        ),
        runtime=Runtime(
            environments={
                "production": Environment(
                    otel_service_name="complete-service-prod",
                    endpoints=["https://api.prod.example.com"],
                    kubernetes=KubernetesRuntime(
                        namespace="prod", deployment="complete-svc"
                    ),
                ),
            }
        ),
        failure_modes=[
            FailureMode(
                mode="upstream-timeout",
                impact="degraded-experience",
                detection="Error rate > 1%",
                recovery="Failover to backup",
                thresholds=FailureModeThresholds(warning_ms=50, critical_ms=100),
            ),
        ],
    )

    # Export then import
    exported = export_graph_json([original])
    imported = import_graph_json(exported)

    # Verify complete preservation
    assert len(imported) == 1
    m = imported[0]

    # System
    assert m.scp == "0.2.0"
    assert m.system.urn == original.system.urn
    assert m.system.name == original.system.name
    assert m.system.description == original.system.description
    assert m.system.version == original.system.version
    assert m.system.classification.tier == 1
    assert m.system.classification.domain == "core"
    assert m.system.classification.tags == ["mission-critical"]

    # Ownership
    assert m.ownership.team == "platform-team"
    assert len(m.ownership.contacts) == 2
    assert m.ownership.escalation == [
        "tech-lead",
        "engineering-manager",
        "vp-engineering",
    ]

    # Capabilities
    assert len(m.provides) == 1
    cap = m.provides[0]
    assert cap.capability == "main-api"
    assert cap.type == "rest"
    assert cap.contract.type == "openapi"
    assert cap.contract.ref == "./api.yaml"
    assert cap.sla.availability == "99.99%"
    assert cap.sla.latency_p99_ms == 100
    assert cap.topics == ["events.published"]

    # Dependencies
    assert len(m.depends) == 1
    dep = m.depends[0]
    assert dep.system == "urn:scp:test:auth-service"
    assert dep.capability == "verify-token"
    assert dep.type == "grpc"
    assert dep.criticality == "required"
    assert dep.failure_mode == "fail-fast"
    assert dep.timeout_ms == 100
    assert dep.retry.max_attempts == 2
    assert dep.retry.backoff == "exponential"

    # Constraints
    assert m.constraints.security.authentication == ["mTLS"]
    assert m.constraints.security.data_classification == "restricted"
    assert m.constraints.compliance.frameworks == ["PCI-DSS"]
    assert m.constraints.compliance.retention_days == 2555
    assert m.constraints.operational.min_replicas == 3
    assert m.constraints.operational.max_replicas == 20

    # Runtime
    assert "production" in m.runtime.environments
    prod = m.runtime.environments["production"]
    assert prod.otel_service_name == "complete-service-prod"
    assert prod.endpoints == ["https://api.prod.example.com"]
    assert prod.kubernetes.namespace == "prod"
    assert prod.kubernetes.deployment == "complete-svc"

    # Failure modes
    assert len(m.failure_modes) == 1
    fm = m.failure_modes[0]
    assert fm.mode == "upstream-timeout"
    assert fm.impact == "degraded-experience"
    assert fm.thresholds.warning_ms == 50
    assert fm.thresholds.critical_ms == 100


def test_roundtrip_with_capability_contract_and_sla():
    """Test that capability contract and SLA survive roundtrip."""
    original = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:api-service", name="API Service"),
        provides=[
            Capability(
                capability="data-api",
                type="graphql",
                contract=Contract(type="graphql", ref="./schema.graphql"),
                sla=SLA(
                    availability="99.9%",
                    latency_p50_ms=25,
                    latency_p99_ms=150,
                    throughput_rps=5000,
                ),
            )
        ],
    )

    exported = export_graph_json([original])
    imported = import_graph_json(exported)

    cap = imported[0].provides[0]
    assert cap.contract.type == "graphql"
    assert cap.contract.ref == "./schema.graphql"
    assert cap.sla.availability == "99.9%"
    assert cap.sla.latency_p50_ms == 25
    assert cap.sla.latency_p99_ms == 150
    assert cap.sla.throughput_rps == 5000


def test_roundtrip_with_dependency_resilience():
    """Test that dependency resilience config survives roundtrip."""
    original = SCPManifest(
        scp="0.1.0",
        system=System(urn="urn:scp:test:consumer", name="Consumer"),
        depends=[
            Dependency(
                system="urn:scp:test:provider",
                capability="events",
                type="event",
                criticality="degraded",
                failure_mode="queue-buffer",
                timeout_ms=10000,
                retry=RetryConfig(max_attempts=5, backoff="linear"),
                circuit_breaker=CircuitBreakerConfig(
                    failure_threshold=10, reset_timeout_ms=60000
                ),
                topics=["orders.created", "orders.updated"],
                access="read",
            )
        ],
    )

    exported = export_graph_json([original])
    imported = import_graph_json(exported)

    dep = imported[0].depends[0]
    assert dep.type == "event"
    assert dep.criticality == "degraded"
    assert dep.failure_mode == "queue-buffer"
    assert dep.timeout_ms == 10000
    assert dep.retry.max_attempts == 5
    assert dep.retry.backoff == "linear"
    assert dep.circuit_breaker.failure_threshold == 10
    assert dep.circuit_breaker.reset_timeout_ms == 60000
    assert dep.topics == ["orders.created", "orders.updated"]
    assert dep.access == "read"
