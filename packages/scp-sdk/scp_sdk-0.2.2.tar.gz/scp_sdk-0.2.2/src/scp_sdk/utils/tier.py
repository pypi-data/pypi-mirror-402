"""Utilities for working with tier classifications.

Tier is a core SCP concept (1-5 scale for criticality). These utilities provide
standardized tier handling and mapping support for integrations.
"""

from typing import Any


class TierUtils:
    """Utilities for working with tier classifications.

    Tier scale (1-5):
    - 1: Critical (highest priority, mission-critical)
    - 2: High (important production systems)
    - 3: Medium (standard production systems)
    - 4: Low (non-critical systems)
    - 5: Planning (experimental/development)
    """

    TIER_NAMES = {
        1: "Critical",
        2: "High",
        3: "Medium",
        4: "Low",
        5: "Planning",
    }

    @staticmethod
    def get_name(tier: int | None) -> str:
        """Get human-readable tier name.

        Args:
            tier: Tier value (1-5) or None

        Returns:
            Tier name or "Unknown" if invalid

        Example:
            >>> TierUtils.get_name(1)
            'Critical'
            >>> TierUtils.get_name(None)
            'Unknown'
        """
        if tier is None:
            return "Unknown"
        return TierUtils.TIER_NAMES.get(tier, "Unknown")

    @staticmethod
    def validate_tier(tier: int | None) -> bool:
        """Check if tier value is valid.

        Args:
            tier: Tier value to validate

        Returns:
            True if valid (1-5) or None, False otherwise

        Example:
            >>> TierUtils.validate_tier(3)
            True
            >>> TierUtils.validate_tier(10)
            False
        """
        return tier is None or (isinstance(tier, int) and 1 <= tier <= 5)

    @staticmethod
    def map_tier(
        tier: int | None, mapping: dict[int, Any], default: Any = "Medium"
    ) -> Any:
        """Map tier to custom value with fallback.

        Useful for integrations that need to map SCP tiers to vendor-specific
        values (e.g., ServiceNow criticality strings).

        Args:
            tier: SCP tier value
            mapping: Custom tier mapping dictionary
            default: Default value if tier not in mapping

        Returns:
            Mapped value or default

        Example:
            >>> mapping = {1: "P0", 2: "P1", 3: "P2"}
            >>> TierUtils.map_tier(1, mapping)
            'P0'
            >>> TierUtils.map_tier(None, mapping, default="P3")
            'P3'
        """
        if tier is None:
            return default
        return mapping.get(tier, default)
