"""Tests for integrations utils module."""

import time

from scp_sdk.integrations.utils import (
    FieldMapper,
    IDCache,
    BatchProcessor,
    CommentBuilder,
)


class TestFieldMapper:
    """Tests for FieldMapper class."""

    def test_map_direct_fields(self):
        """Should map direct SCP fields to vendor fields."""
        mapping = {"ci_name": "name", "ci_tier": "tier"}
        mapper = FieldMapper(mapping)

        scp_data = {"name": "Service A", "tier": 2, "other": "ignored"}
        result = mapper.map_fields(scp_data)

        assert result["ci_name"] == "Service A"
        assert result["ci_tier"] == 2
        assert "other" not in result

    def test_skip_none_values(self):
        """Should skip None values."""
        mapping = {"ci_name": "name"}
        mapper = FieldMapper(mapping)

        scp_data = {"name": None}
        result = mapper.map_fields(scp_data)

        assert "ci_name" not in result

    def test_extract_nested_value(self):
        """Should extract nested values with dot notation."""
        mapper = FieldMapper({})
        scp_data = {"system": {"tier": 2, "name": "Test"}}

        assert mapper.extract_value(scp_data, "system.tier") == 2
        assert mapper.extract_value(scp_data, "system.name") == "Test"

    def test_extract_missing_path(self):
        """Should return None for missing paths."""
        mapper = FieldMapper({})
        scp_data = {"system": {"tier": 2}}

        assert mapper.extract_value(scp_data, "system.missing") is None
        assert mapper.extract_value(scp_data, "nonexistent.path") is None


class TestIDCache:
    """Tests for IDCache class."""

    def test_get_cached_id(self):
        """Should return cached vendor ID."""
        cache = IDCache()
        cache.set("urn:scp:test:a", "vendor_id_123")

        assert cache.get("urn:scp:test:a") == "vendor_id_123"

    def test_get_uncached_id(self):
        """Should return None for uncached URN."""
        cache = IDCache()
        assert cache.get("urn:scp:test:unknown") is None

    def test_get_or_fetch_cached(self):
        """Should return cached value without calling fetch."""
        cache = IDCache()
        cache.set("urn:scp:test:a", "cached_id")

        fetch_called = False

        def fetch_fn(urn):
            nonlocal fetch_called
            fetch_called = True
            return "fetched_id"

        result = cache.get_or_fetch("urn:scp:test:a", fetch_fn)
        assert result == "cached_id"
        assert not fetch_called

    def test_get_or_fetch_not_cached(self):
        """Should fetch and cache if not present."""
        cache = IDCache()

        def fetch_fn(urn):
            return "fetched_id"

        result = cache.get_or_fetch("urn:scp:test:b", fetch_fn)
        assert result == "fetched_id"
        assert cache.get("urn:scp:test:b") == "fetched_id"

    def test_clear(self):
        """Should clear all cached IDs."""
        cache = IDCache()
        cache.set("urn:scp:test:a", "id1")
        cache.set("urn:scp:test:b", "id2")

        cache.clear()

        assert cache.get("urn:scp:test:a") is None
        assert cache.get("urn:scp:test:b") is None


class TestBatchProcessor:
    """Tests for BatchProcessor class."""

    def test_process_in_batches(self):
        """Should process items in batches."""
        processor = BatchProcessor(batch_size=2)
        items = [1, 2, 3, 4, 5]
        batches = []

        def process_fn(batch):
            batches.append(batch)

        processor.process(items, process_fn)

        assert len(batches) == 3
        assert batches[0] == [1, 2]
        assert batches[1] == [3, 4]
        assert batches[2] == [5]

    def test_rate_limiting(self):
        """Should apply delay between batches."""
        processor = BatchProcessor(batch_size=2, delay_seconds=0.1)
        items = [1, 2, 3, 4]

        start = time.time()
        processor.process(items, lambda batch: None)
        duration = time.time() - start

        # Should have at least one delay (between batch 1 and 2)
        assert duration >= 0.1


class TestCommentBuilder:
    """Tests for CommentBuilder class."""

    def test_build_with_default_template(self):
        """Should build comment with default template."""
        builder = CommentBuilder()
        data = {
            "team": "platform",
            "domain": "payments",
            "contacts": [{"type": "email", "ref": "team@example.com"}],
            "escalation": ["lead", "manager"],
        }

        comment = builder.build(data)

        assert "Team: platform" in comment
        assert "Domain: payments" in comment
        assert "email: team@example.com" in comment
        assert "lead → manager" in comment

    def test_build_with_missing_data(self):
        """Should handle missing data gracefully."""
        builder = CommentBuilder()
        data = {}

        comment = builder.build(data)

        assert "Team: N/A" in comment
        assert "Domain: N/A" in comment
