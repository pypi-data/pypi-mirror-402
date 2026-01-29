"""Export and import functions for SCP graph data.

This module provides vendor-neutral export/import for the unified JSON graph format,
enabling integration interchange and transformation workflows.
"""

from typing import Any

from .models import (
    SCPManifest,
    System,
    Classification,
    Ownership,
    Contact,
    Capability,
    Dependency,
    SecurityExtension,
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
)


def _serialize_contract(contract: Contract | None) -> dict[str, Any] | None:
    """Serialize Contract to dict."""
    if not contract:
        return None
    return {"type": contract.type, "ref": contract.ref}


def _serialize_sla(sla: SLA | None) -> dict[str, Any] | None:
    """Serialize SLA to dict."""
    if not sla:
        return None
    return {
        "availability": sla.availability,
        "latency_p50_ms": sla.latency_p50_ms,
        "latency_p99_ms": sla.latency_p99_ms,
        "throughput_rps": sla.throughput_rps,
    }


def _serialize_retry(retry: RetryConfig | None) -> dict[str, Any] | None:
    """Serialize RetryConfig to dict."""
    if not retry:
        return None
    return {"max_attempts": retry.max_attempts, "backoff": retry.backoff}


def _serialize_circuit_breaker(
    cb: CircuitBreakerConfig | None,
) -> dict[str, Any] | None:
    """Serialize CircuitBreakerConfig to dict."""
    if not cb:
        return None
    return {
        "failure_threshold": cb.failure_threshold,
        "reset_timeout_ms": cb.reset_timeout_ms,
    }


def _serialize_constraints(constraints: Constraints | None) -> dict[str, Any] | None:
    """Serialize Constraints to dict."""
    if not constraints:
        return None
    result: dict[str, Any] = {}
    if constraints.security:
        result["security"] = {
            "authentication": constraints.security.authentication,
            "data_classification": constraints.security.data_classification,
            "encryption": constraints.security.encryption,
        }
    if constraints.compliance:
        result["compliance"] = {
            "frameworks": constraints.compliance.frameworks,
            "data_residency": constraints.compliance.data_residency,
            "retention_days": constraints.compliance.retention_days,
        }
    if constraints.operational:
        result["operational"] = {
            "max_replicas": constraints.operational.max_replicas,
            "min_replicas": constraints.operational.min_replicas,
            "deployment_windows": constraints.operational.deployment_windows,
        }
    return result if result else None


def _serialize_runtime(runtime: Runtime | None) -> dict[str, Any] | None:
    """Serialize Runtime to dict."""
    if not runtime or not runtime.environments:
        return None
    envs: dict[str, Any] = {}
    for name, env in runtime.environments.items():
        env_data: dict[str, Any] = {
            "otel_service_name": env.otel_service_name,
            "endpoints": env.endpoints,
        }
        if env.kubernetes:
            env_data["kubernetes"] = {
                "namespace": env.kubernetes.namespace,
                "deployment": env.kubernetes.deployment,
                "service": env.kubernetes.service,
            }
        if env.aws:
            env_data["aws"] = {
                "account_id": env.aws.account_id,
                "region": env.aws.region,
                "arn": env.aws.arn,
            }
        envs[name] = env_data
    return {"environments": envs}


def _serialize_failure_modes(
    failure_modes: list[FailureMode] | None,
) -> list[dict[str, Any]] | None:
    """Serialize FailureModes to list of dicts."""
    if not failure_modes:
        return None
    result = []
    for fm in failure_modes:
        fm_data: dict[str, Any] = {
            "mode": fm.mode,
            "impact": fm.impact,
            "detection": fm.detection,
            "recovery": fm.recovery,
            "degraded_behavior": fm.degraded_behavior,
            "mttr_target_minutes": fm.mttr_target_minutes,
        }
        if fm.thresholds:
            fm_data["thresholds"] = {
                "warning_ms": fm.thresholds.warning_ms,
                "critical_ms": fm.thresholds.critical_ms,
            }
        result.append(fm_data)
    return result


def export_graph_json(manifests: list[SCPManifest]) -> dict[str, Any]:
    """Export manifests to unified JSON graph format.

    Creates a standardized graph representation with nodes and edges that
    can be consumed by integrations, visualizations, and analysis tools.

    This export includes ALL manifest data for complete roundtrip fidelity.
    System nodes are deduplicated (last wins), and stub nodes are created
    for external dependencies.

    Args:
        manifests: List of SCP manifests to export

    Returns:
        Dictionary with 'nodes', 'edges', and 'meta' keys:
            - nodes: List of system and capability nodes with full data
            - edges: List of dependency and provides edges with resilience config
            - meta: Counts and statistics

    Example:
        >>> from scp_sdk import Manifest, export_graph_json
        >>> manifests = [Manifest.from_file("scp.yaml")]
        >>> graph_data = export_graph_json(manifests)
        >>>
        >>> # Save to file
        >>> import json
        >>> with open("graph.json", "w") as f:
        ...     json.dump(graph_data, f, indent=2)
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    system_nodes: dict[str, dict] = {}  # Track by URN for stub replacement

    for manifest in manifests:
        urn = manifest.system.urn

        # Build complete system node with ALL fields
        system_node: dict[str, Any] = {
            "id": urn,
            "type": "System",
            "name": manifest.system.name,
            "description": manifest.system.description,
            "version": manifest.system.version,
            "scp_version": manifest.scp,
            # Classification fields
            "tier": manifest.system.classification.tier
            if manifest.system.classification
            else None,
            "domain": manifest.system.classification.domain
            if manifest.system.classification
            else None,
            "tags": manifest.system.classification.tags
            if manifest.system.classification
            else None,
            # Ownership fields
            "team": manifest.ownership.team if manifest.ownership else None,
            "contacts": [
                {"type": c.type, "ref": c.ref} for c in manifest.ownership.contacts
            ]
            if manifest.ownership and manifest.ownership.contacts
            else [],
            "escalation": manifest.ownership.escalation if manifest.ownership else [],
            # Complex sections
            "constraints": _serialize_constraints(manifest.constraints),
            "runtime": _serialize_runtime(manifest.runtime),
            "failure_modes": _serialize_failure_modes(manifest.failure_modes),
        }
        system_nodes[urn] = system_node

        # Add dependency edges with full resilience config
        if manifest.depends:
            for dep in manifest.depends:
                # Create stub node for dependency target if not seen
                if dep.system not in system_nodes:
                    system_nodes[dep.system] = {
                        "id": dep.system,
                        "type": "System",
                        "name": dep.system.split(":")[-1],  # Extract name from URN
                        "stub": True,
                    }

                edges.append(
                    {
                        "from": urn,
                        "to": dep.system,
                        "type": "DEPENDS_ON",
                        "capability": dep.capability,
                        "dependency_type": dep.type,
                        "criticality": dep.criticality,
                        "failure_mode": dep.failure_mode,
                        "timeout_ms": dep.timeout_ms,
                        "retry": _serialize_retry(dep.retry),
                        "circuit_breaker": _serialize_circuit_breaker(
                            dep.circuit_breaker
                        ),
                        "topics": dep.topics,
                        "access": dep.access,
                    }
                )

        # Add capability nodes with full contract/SLA data and PROVIDES edges
        if manifest.provides:
            for cap in manifest.provides:
                cap_id = f"{urn}:{cap.capability}"
                cap_node: dict[str, Any] = {
                    "id": cap_id,
                    "type": "Capability",
                    "name": cap.capability,
                    "capability_type": cap.type,
                    "contract": _serialize_contract(cap.contract),
                    "sla": _serialize_sla(cap.sla),
                    "topics": cap.topics,
                }
                # Include security extension if present
                if cap.x_security:
                    cap_node["x_security"] = {
                        "actuator_profile": cap.x_security.actuator_profile,
                        "actions": cap.x_security.actions,
                        "targets": cap.x_security.targets,
                    }
                nodes.append(cap_node)
                edges.append(
                    {
                        "from": urn,
                        "to": cap_id,
                        "type": "PROVIDES",
                    }
                )

    # Combine system nodes (from dict) with capability nodes (from list)
    all_nodes = list(system_nodes.values()) + nodes

    return {
        "nodes": all_nodes,
        "edges": edges,
        "meta": {
            "systems_count": len(system_nodes),
            "capabilities_count": len(nodes),
            "dependencies_count": len([e for e in edges if e["type"] == "DEPENDS_ON"]),
        },
    }


def import_graph_json(data: dict[str, Any]) -> list[SCPManifest]:
    """Import manifests from unified JSON graph format.

    Reconstructs SCPManifest objects from the export_graph_json() format,
    enabling transformation workflows without re-scanning source manifests.

    Stub nodes (external dependencies) are ignored during reconstruction.
    This import restores ALL fields that were exported for complete roundtrip fidelity.

    Args:
        data: Dictionary from export_graph_json() output, containing 'nodes' and 'edges'

    Returns:
        List of reconstructed SCP manifests

    Raises:
        ValueError: If data format is invalid or missing required fields

    Example:
        >>> import json
        >>> from scp_sdk import import_graph_json
        >>>
        >>> with open("graph.json") as f:
        ...     data = json.load(f)
        >>>
        >>> manifests = import_graph_json(data)
        >>> for manifest in manifests:
        ...     print(f"Loaded {manifest.system.name}")
    """
    manifests: list[SCPManifest] = []
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    # Build lookup maps
    system_nodes = {
        n["id"]: n for n in nodes if n.get("type") == "System" and not n.get("stub")
    }
    capability_nodes = {n["id"]: n for n in nodes if n.get("type") == "Capability"}

    # Group edges by source system
    provides_by_system: dict[str, list[dict]] = {}
    depends_by_system: dict[str, list[dict]] = {}

    for edge in edges:
        if edge["type"] == "PROVIDES":
            provides_by_system.setdefault(edge["from"], []).append(edge)
        elif edge["type"] == "DEPENDS_ON":
            depends_by_system.setdefault(edge["from"], []).append(edge)

    # Reconstruct manifests
    for urn, node in system_nodes.items():
        # Build classification
        classification = None
        if node.get("tier") or node.get("domain") or node.get("tags"):
            classification = Classification(
                tier=node.get("tier"),
                domain=node.get("domain"),
                tags=node.get("tags"),
            )

        # Build ownership
        ownership = None
        if node.get("team"):
            contacts = []
            if node.get("contacts"):
                for c in node["contacts"]:
                    contacts.append(Contact(type=c["type"], ref=c["ref"]))

            ownership = Ownership(
                team=node["team"],
                contacts=contacts if contacts else None,
                escalation=node.get("escalation"),
            )

        # Build constraints
        constraints = None
        if node.get("constraints"):
            c = node["constraints"]
            security = None
            compliance = None
            operational = None

            if c.get("security"):
                s = c["security"]
                security = SecurityConstraints(
                    authentication=s.get("authentication"),
                    data_classification=s.get("data_classification"),
                    encryption=s.get("encryption"),
                )
            if c.get("compliance"):
                comp = c["compliance"]
                compliance = ComplianceConstraints(
                    frameworks=comp.get("frameworks"),
                    data_residency=comp.get("data_residency"),
                    retention_days=comp.get("retention_days"),
                )
            if c.get("operational"):
                op = c["operational"]
                operational = OperationalConstraints(
                    max_replicas=op.get("max_replicas"),
                    min_replicas=op.get("min_replicas"),
                    deployment_windows=op.get("deployment_windows"),
                )

            if security or compliance or operational:
                constraints = Constraints(
                    security=security,
                    compliance=compliance,
                    operational=operational,
                )

        # Build runtime
        runtime = None
        if node.get("runtime") and node["runtime"].get("environments"):
            envs: dict[str, Environment] = {}
            for env_name, env_data in node["runtime"]["environments"].items():
                k8s = None
                aws = None
                if env_data.get("kubernetes"):
                    k = env_data["kubernetes"]
                    k8s = KubernetesRuntime(
                        namespace=k.get("namespace"),
                        deployment=k.get("deployment"),
                        service=k.get("service"),
                    )
                if env_data.get("aws"):
                    a = env_data["aws"]
                    aws = AWSRuntime(
                        account_id=a.get("account_id"),
                        region=a.get("region"),
                        arn=a.get("arn"),
                    )
                envs[env_name] = Environment(
                    otel_service_name=env_data.get("otel_service_name"),
                    endpoints=env_data.get("endpoints"),
                    kubernetes=k8s,
                    aws=aws,
                )
            runtime = Runtime(environments=envs)

        # Build failure modes
        failure_modes = None
        if node.get("failure_modes"):
            failure_modes = []
            for fm in node["failure_modes"]:
                thresholds = None
                if fm.get("thresholds"):
                    thresholds = FailureModeThresholds(
                        warning_ms=fm["thresholds"].get("warning_ms"),
                        critical_ms=fm["thresholds"].get("critical_ms"),
                    )
                failure_modes.append(
                    FailureMode(
                        mode=fm["mode"],
                        impact=fm["impact"],
                        detection=fm.get("detection"),
                        recovery=fm.get("recovery"),
                        degraded_behavior=fm.get("degraded_behavior"),
                        mttr_target_minutes=fm.get("mttr_target_minutes"),
                        thresholds=thresholds,
                    )
                )

        # Build capabilities
        provides = []
        for edge in provides_by_system.get(urn, []):
            cap_node = capability_nodes.get(edge["to"])
            if cap_node:
                # Rebuild security extension if present
                x_security = None
                if cap_node.get("x_security"):
                    sec = cap_node["x_security"]
                    x_security = SecurityExtension(
                        actuator_profile=sec.get("actuator_profile"),
                        actions=sec.get("actions", []),
                        targets=sec.get("targets", []),
                    )

                # Rebuild contract if present
                contract = None
                if cap_node.get("contract"):
                    cont = cap_node["contract"]
                    contract = Contract(type=cont.get("type"), ref=cont.get("ref"))

                # Rebuild SLA if present
                sla = None
                if cap_node.get("sla"):
                    s = cap_node["sla"]
                    sla = SLA(
                        availability=s.get("availability"),
                        latency_p50_ms=s.get("latency_p50_ms"),
                        latency_p99_ms=s.get("latency_p99_ms"),
                        throughput_rps=s.get("throughput_rps"),
                    )

                cap_data: dict[str, Any] = {
                    "capability": cap_node["name"],
                    "type": cap_node.get("capability_type", "rest"),
                    "topics": cap_node.get("topics"),
                }
                if x_security:
                    cap_data["x-security"] = x_security
                if contract:
                    cap_data["contract"] = contract
                if sla:
                    cap_data["sla"] = sla
                provides.append(Capability.model_validate(cap_data))

        # Build dependencies
        depends = []
        for edge in depends_by_system.get(urn, []):
            # Rebuild retry config if present
            retry = None
            if edge.get("retry"):
                r = edge["retry"]
                retry = RetryConfig(
                    max_attempts=r.get("max_attempts"),
                    backoff=r.get("backoff"),
                )

            # Rebuild circuit breaker if present
            circuit_breaker = None
            if edge.get("circuit_breaker"):
                cb = edge["circuit_breaker"]
                circuit_breaker = CircuitBreakerConfig(
                    failure_threshold=cb.get("failure_threshold"),
                    reset_timeout_ms=cb.get("reset_timeout_ms"),
                )

            depends.append(
                Dependency(
                    system=edge["to"],
                    capability=edge.get("capability"),
                    type=edge.get("dependency_type", "rest"),
                    criticality=edge.get("criticality", "required"),
                    failure_mode=edge.get("failure_mode"),
                    timeout_ms=edge.get("timeout_ms"),
                    retry=retry,
                    circuit_breaker=circuit_breaker,
                    topics=edge.get("topics"),
                    access=edge.get("access"),
                )
            )

        manifest = SCPManifest(
            scp=node.get("scp_version", "0.1.0"),
            system=System(
                urn=urn,
                name=node["name"],
                description=node.get("description"),
                version=node.get("version"),
                classification=classification,
            ),
            ownership=ownership,
            provides=provides if provides else None,
            depends=depends if depends else None,
            constraints=constraints,
            runtime=runtime,
            failure_modes=failure_modes if failure_modes else None,
        )
        manifests.append(manifest)

    return manifests
