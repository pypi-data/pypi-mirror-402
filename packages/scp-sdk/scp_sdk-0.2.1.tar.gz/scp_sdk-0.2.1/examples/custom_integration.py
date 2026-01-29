"""Example custom integration using the SDK - PagerDuty integration."""

from scp_sdk.core.graph import SystemNode, DependencyEdge
from scp_sdk.integrations.base import IntegrationBase
from scp_sdk.integrations.config import IntegrationConfig
from scp_sdk.integrations.registry import register_integration


@register_integration("pagerduty")
class PagerDutyIntegration(IntegrationBase):
    """Example PagerDuty integration using SDK framework.

    This demonstrates how easy it is to build an integration
    when using the SDK's base class and utilities.
    """

    def sync_system(self, system: SystemNode) -> None:
        """Sync a system to PagerDuty as a service.

        Args:
            system: System to sync
        """
        self.logger.info(f"Syncing system to PagerDuty: {system.name}")

        # Map SCP data to PagerDuty format
        _service_data = {
            "name": system.name,
            "description": f"SCP System: {system.urn}",
            # Use escalation from SCP if available
            "escalation_policy": self._get_escalation_policy(system),
            "alert_creation": "create_alerts_and_incidents",
        }

        # In a real integration, you would:
        # 1. Call PagerDuty API to create/update service
        # 2. Cache the PagerDuty service ID
        # self.cache_vendor_id(system.urn, pd_service_id)

        # Simulated for example
        pd_service_id = f"pd_{system.urn.replace(':', '_')}"
        self.cache_vendor_id(system.urn, pd_service_id)

        self.logger.debug(f"  → Created/updated service: {pd_service_id}")

    def sync_dependency(self, edge: DependencyEdge) -> None:
        """Sync dependency (PagerDuty doesn't have explicit dependencies).

        Args:
            edge: Dependency edge
        """
        # PagerDuty doesn't have a dependencies concept
        # Could potentially use this to set up service dependencies
        # or cross-references in the future
        self.logger.debug(
            f"Skipping dependency (not supported): {edge.from_urn} -> {edge.to_urn}"
        )

    def _get_escalation_policy(self, system: SystemNode) -> str:
        """Get or create escalation policy for system.

        Args:
            system: System node

        Returns:
            Escalation policy ID
        """
        # In real implementation, would map team to escalation policy
        # For example: look up by system.team or system.escalation
        if system.escalation and len(system.escalation) > 0:
            policy_name = f"escalation_{system.escalation[0]}"
        elif system.team:
            policy_name = f"escalation_{system.team}"
        else:
            policy_name = "default_escalation"

        return policy_name


def main():
    """Demonstrate using the PagerDuty integration."""
    print("=== PagerDuty Integration Example ===\n")

    # Create config
    config = IntegrationConfig(
        name="pagerduty",
        vendor="PagerDuty",
        # In real usage, would have auth config:
        # auth=AuthConfig(api_key="${PAGERDUTY_API_KEY}")
    )

    # Create integration instance
    integration = PagerDutyIntegration(config)

    # Create some example systems
    from scp_sdk.core.graph import Graph

    system1 = SystemNode(
        urn="urn:scp:payment-service",
        name="Payment Service",
        tier=1,
        team="payments-platform",
        escalation=["payments-platform", "platform-leads"],
    )

    system2 = SystemNode(
        urn="urn:scp:user-service",
        name="User Service",
        tier=1,
        team="identity-platform",
    )

    edge = DependencyEdge(
        from_urn="urn:scp:payment-service",
        to_urn="urn:scp:user-service",
        criticality="required",
    )

    graph = Graph(systems=[system1, system2], edges=[edge])

    # Sync to PagerDuty (dry run)
    print("Running sync in dry-run mode...")
    result = integration.sync(graph, dry_run=True)

    print("\nResults:")
    print(f"  Systems synced: {result.systems_synced}")
    print(f"  Dependencies synced: {result.dependencies_synced}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Success: {result.success}")

    print("\n✓ Integration example complete!")
    print("\nThis demonstrates how the SDK makes building integrations simple:")
    print("  - Just implement sync_system() and sync_dependency()")
    print("  - Base class handles iteration, error handling, logging")
    print("  - Utilities (IDCache, FieldMapper) available")
    print("  - ~50 lines of code vs ~700 without SDK!")


if __name__ == "__main__":
    main()
