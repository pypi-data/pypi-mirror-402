"""Tests for tier utilities."""

from scp_sdk import TierUtils


class TestTierUtils:
    """Tests for TierUtils class."""

    def test_tier_names(self):
        """Should have correct tier name mappings."""
        assert TierUtils.TIER_NAMES[1] == "Critical"
        assert TierUtils.TIER_NAMES[2] == "High"
        assert TierUtils.TIER_NAMES[3] == "Medium"
        assert TierUtils.TIER_NAMES[4] == "Low"
        assert TierUtils.TIER_NAMES[5] == "Planning"

    def test_get_name_valid(self):
        """Should return correct names for valid tiers."""
        assert TierUtils.get_name(1) == "Critical"
        assert TierUtils.get_name(3) == "Medium"
        assert TierUtils.get_name(5) == "Planning"

    def test_get_name_none(self):
        """Should return Unknown for None."""
        assert TierUtils.get_name(None) == "Unknown"

    def test_get_name_invalid(self):
        """Should return Unknown for invalid tiers."""
        assert TierUtils.get_name(0) == "Unknown"
        assert TierUtils.get_name(10) == "Unknown"
        assert TierUtils.get_name(-1) == "Unknown"

    def test_validate_tier_valid(self):
        """Should validate correct tier values."""
        assert TierUtils.validate_tier(1) is True
        assert TierUtils.validate_tier(3) is True
        assert TierUtils.validate_tier(5) is True

    def test_validate_tier_none(self):
        """Should accept None as valid."""
        assert TierUtils.validate_tier(None) is True

    def test_validate_tier_invalid(self):
        """Should reject invalid tier values."""
        assert TierUtils.validate_tier(0) is False
        assert TierUtils.validate_tier(6) is False
        assert TierUtils.validate_tier(10) is False
        assert TierUtils.validate_tier(-1) is False

    def test_map_tier_with_mapping(self):
        """Should map tier using custom mapping."""
        mapping = {1: "P0", 2: "P1", 3: "P2"}
        assert TierUtils.map_tier(1, mapping) == "P0"
        assert TierUtils.map_tier(2, mapping) == "P1"
        assert TierUtils.map_tier(3, mapping) == "P2"

    def test_map_tier_default(self):
        """Should use default for unmapped tiers."""
        mapping = {1: "P0", 2: "P1"}
        assert TierUtils.map_tier(3, mapping, default="P3") == "P3"
        assert TierUtils.map_tier(None, mapping, default="P3") == "P3"

    def test_map_tier_servicenow_pattern(self):
        """Should work with ServiceNow-style criticality mapping."""
        mapping = {
            1: "1 - Critical",
            2: "2 - High",
            3: "3 - Medium",
            4: "4 - Low",
            5: "5 - Planning",
        }
        assert TierUtils.map_tier(1, mapping) == "1 - Critical"
        assert TierUtils.map_tier(3, mapping) == "3 - Medium"
